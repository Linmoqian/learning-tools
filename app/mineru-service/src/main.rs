use actix_files::NamedFile;
use actix_multipart::Multipart;
use actix_web::{get, post, web, App, HttpServer, middleware, HttpResponse, Result};
use futures_util::StreamExt;
use log::{error, info, warn};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::io::Read;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

// ===== 配置 =====

struct AppConfig {
    mineru_api_url: String,
    mineru_api_key: String,
    output_dir: PathBuf,
    http_client: Client,
}

struct AppState {
    config: Mutex<AppConfig>,
}

// ===== API 类型 =====

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    mineru: bool,
}

#[derive(Serialize)]
struct ConvertResponse {
    name: String,
    title: String,
    content: String,
    images: Vec<String>,
}

#[derive(Deserialize)]
struct MinerUBatchResponse {
    code: i32,
    msg: Option<String>,
    data: Option<MinerUBatchData>,
}

#[derive(Deserialize)]
struct MinerUBatchData {
    batch_id: String,
    file_urls: Vec<String>,
}

#[derive(Deserialize)]
struct MinerUResultResponse {
    code: i32,
    msg: Option<String>,
    data: Option<MinerUResultData>,
}

#[derive(Deserialize)]
struct MinerUResultData {
    extract_result: Vec<MinerUExtractItem>,
}

#[derive(Deserialize)]
struct MinerUExtractItem {
    data_id: String,
    state: String,
    err_msg: Option<String>,
    full_zip_url: Option<String>,
    extract_progress: Option<MinerUProgress>,
}

#[derive(Deserialize)]
struct MinerUProgress {
    extracted_pages: Option<i32>,
    total_pages: Option<i32>,
}

#[derive(Serialize, Deserialize)]
struct FileUrlRequest {
    model_version: String,
    enable_formula: bool,
    enable_table: bool,
    language: String,
    files: Vec<FileItem>,
}

#[derive(Serialize, Deserialize)]
struct FileItem {
    name: String,
    data_id: String,
}

// ===== 健康检查 =====

#[get("/health")]
async fn health() -> HttpResponse {
    HttpResponse::Ok().json(HealthResponse {
        status: "ok".into(),
        mineru: true,
    })
}

// ===== 图片服务 =====

#[get("/images/{filename}")]
async fn serve_image(state: web::Data<AppState>, path: web::Path<String>) -> Result<NamedFile> {
    let filename = path.into_inner();
    let output_dir = {
        let cfg = state.config.lock().unwrap();
        cfg.output_dir.join("images")
    };
    let filepath = output_dir.join(&filename);

    match NamedFile::open(&filepath) {
        Ok(f) => Ok(f),
        Err(e) => {
            error!("图片文件不存在: {:?} ({})", filepath, e);
            Err(actix_web::error::ErrorNotFound("图片不存在"))
        }
    }
}

// ===== 文件转换 =====

#[post("/convert")]
async fn convert(
    state: web::Data<AppState>,
    mut payload: Multipart,
) -> Result<HttpResponse, actix_web::Error> {
    // 1. 从 multipart 读取文件
    let mut file_bytes: Vec<u8> = Vec::new();
    let mut file_name = String::new();

    while let Some(item) = payload.next().await {
        let mut field = item.map_err(|e| {
            error!("读取 multipart 失败: {}", e);
            actix_web::error::ErrorBadRequest("读取上传文件失败")
        })?;

        if let Some(cd) = field.content_disposition() {
            if let Some(fname) = cd.get_filename() {
                file_name = fname.to_string();
            }
        }

        while let Some(chunk) = field.next().await {
            let data = chunk.map_err(|_| actix_web::error::ErrorBadRequest("读取分块失败"))?;
            file_bytes.extend_from_slice(&data);
        }
    }

    if file_bytes.is_empty() {
        return Err(actix_web::error::ErrorBadRequest("未提供文件"));
    }

    let stem = Path::new(&file_name)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("unknown")
        .to_string();

    info!("收到文件: {} ({} bytes)", file_name, file_bytes.len());

    // 2. 获取 MinerU API 配置
    let (api_url, api_key) = {
        let cfg = state.config.lock().unwrap();
        (cfg.mineru_api_url.clone(), cfg.mineru_api_key.clone())
    };

    if api_key.is_empty() {
        return Err(actix_web::error::ErrorBadRequest(
            "MinerU API Key 未配置，请在环境变量 MINERU_API_KEY 中设置",
        ));
    }

    let client = {
        let cfg = state.config.lock().unwrap();
        cfg.http_client.clone()
    };

    let auth_header = format!("Bearer {}", api_key);

    // 3. 请求上传链接
    let file_url_req = FileUrlRequest {
        model_version: "vlm".into(),
        enable_formula: true,
        enable_table: true,
        language: "ch".into(),
        files: vec![FileItem {
            name: file_name.clone(),
            data_id: stem.clone(),
        }],
    };

    let batch_resp = client
        .post(format!("{}/api/v4/file-urls/batch", api_url))
        .header("Content-Type", "application/json")
        .header("Authorization", &auth_header)
        .json(&file_url_req)
        .send()
        .await
        .map_err(|e| {
            error!("请求上传链接失败: {}", e);
            actix_web::error::ErrorInternalServerError("无法连接 MinerU API")
        })?;

    let batch_data: MinerUBatchResponse = batch_resp.json().await.map_err(|e| {
        error!("解析上传链接响应失败: {}", e);
        actix_web::error::ErrorInternalServerError("MinerU API 响应格式错误")
    })?;

    if batch_data.code != 0 {
        let msg = batch_data.msg.unwrap_or_else(|| "未知错误".into());
        error!("MinerU API 错误: {}", msg);
        return Err(actix_web::error::ErrorInternalServerError(msg));
    }

    let batch_id = batch_data
        .data
        .as_ref()
        .map(|d| d.batch_id.clone())
        .unwrap_or_default();
    let upload_url = batch_data
        .data
        .as_ref()
        .and_then(|d| d.file_urls.first().cloned())
        .ok_or_else(|| actix_web::error::ErrorInternalServerError("未获取到上传链接"))?;

    info!("Batch ID: {}, 开始上传...", batch_id);

    // 4. 上传文件
    let upload_resp = client
        .put(&upload_url)
        .body(file_bytes.clone())
        .send()
        .await
        .map_err(|e| {
            error!("文件上传失败: {}", e);
            actix_web::error::ErrorInternalServerError("文件上传失败")
        })?;

    if !upload_resp.status().is_success() {
        return Err(actix_web::error::ErrorInternalServerError(format!(
            "文件上传失败: HTTP {}",
            upload_resp.status()
        )));
    }

    info!("文件上传完成，开始轮询结果...");

    // 5. 轮询结果（使用 'outer 标签 loop 配合可变变量）
    let mut zip_url: Option<String> = None;
    let mut poll_error: Option<String> = None;

    'poll: loop {
        let poll_resp = client
            .get(format!("{}/api/v4/extract-results/batch/{}", api_url, batch_id))
            .header("Authorization", &auth_header)
            .send()
            .await
            .map_err(|e| {
                error!("查询结果失败: {}", e);
                actix_web::error::ErrorInternalServerError("查询转换结果失败")
            })?;

        let poll_data: MinerUResultResponse = poll_resp.json().await.map_err(|e| {
            error!("解析结果响应失败: {}", e);
            actix_web::error::ErrorInternalServerError("结果响应格式错误")
        })?;

        if poll_data.code != 0 {
            let msg = poll_data.msg.unwrap_or_else(|| "未知错误".into());
            poll_error = Some(msg.clone());
            error!("查询结果错误: {}", msg);
            break 'poll;
        }

        let items = poll_data
            .data
            .map(|d| d.extract_result)
            .unwrap_or_default();

        let mut found = false;
        for item in &items {
            if item.data_id == stem {
                found = true;
                match item.state.as_str() {
                    "done" => {
                        zip_url = item.full_zip_url.clone();
                        break 'poll;
                    }
                    "failed" => {
                        let err = item.err_msg.as_deref().unwrap_or("未知错误");
                        poll_error = Some(err.to_string());
                        error!("转换失败: {}", err);
                        break 'poll;
                    }
                    _ => {
                        let p = item.extract_progress.as_ref();
                        let progress = p
                            .map(|pr| {
                                format!(
                                    "{}/{}",
                                    pr.extracted_pages.unwrap_or(0),
                                    pr.total_pages.unwrap_or(0)
                                )
                            })
                            .unwrap_or_else(|| "等待中".into());
                        info!("  [{}] {}", item.state, progress);
                    }
                }
            }
        }

        if !found {
            info!("  data_id {} 未在结果中, 继续等待...", stem);
        }

        tokio::time::sleep(std::time::Duration::from_secs(3)).await;
    }

    if let Some(err) = poll_error {
        return Err(actix_web::error::ErrorInternalServerError(err));
    }

    let zip_url = zip_url.ok_or_else(|| {
        actix_web::error::ErrorInternalServerError("未获取到下载链接")
    })?;

    info!("转换完成，开始下载结果...");

    // 6. 下载 zip
    let zip_resp = client
        .get(&zip_url)
        .send()
        .await
        .map_err(|e| {
            error!("下载结果失败: {}", e);
            actix_web::error::ErrorInternalServerError("下载转换结果失败")
        })?;

    let zip_bytes = zip_resp.bytes().await.map_err(|e| {
        error!("读取结果数据失败: {}", e);
        actix_web::error::ErrorInternalServerError("读取转换结果失败")
    })?;

    // 7. 解压并提取内容
    let output_dir = {
        let cfg = state.config.lock().unwrap();
        cfg.output_dir.clone()
    };
    let images_dir = output_dir.join("images");
    std::fs::create_dir_all(&images_dir).ok();

    let cursor = std::io::Cursor::new(&zip_bytes);
    let mut archive = zip::ZipArchive::new(cursor).map_err(|e| {
        error!("解压失败: {}", e);
        actix_web::error::ErrorInternalServerError("解压结果文件失败")
    })?;

    let mut md_content = String::new();
    let mut image_files: Vec<String> = Vec::new();

    for i in 0..archive.len() {
        let mut file = archive.by_index(i).map_err(|e| {
            error!("读取 zip 条目失败: {}", e);
            actix_web::error::ErrorInternalServerError("读取压缩包失败")
        })?;

        let out_path = file.name().to_string();

        if out_path.ends_with(".md") {
            let mut content = String::new();
            file.read_to_string(&mut content).ok();
            md_content = content;
        } else if out_path.starts_with("images/") || out_path.starts_with("images\\") {
            let img_name = Path::new(&out_path)
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_string();
            if !img_name.is_empty() {
                let dest_name = format!("{}-{}", stem, img_name);
                let dest_path = images_dir.join(&dest_name);
                if let Ok(mut f) = std::fs::File::create(&dest_path) {
                    use std::io::Write;
                    let mut data = Vec::new();
                    file.read_to_end(&mut data).ok();
                    f.write_all(&data).ok();
                    image_files.push(dest_name);
                }
            }
        }
    }

    // 8. 保存 MD 文件
    if !md_content.is_empty() {
        let md_path = output_dir.join(format!("{}.md", stem));
        std::fs::write(&md_path, &md_content).ok();
    }

    info!("转换完成: {}, 图片 {} 张", file_name, image_files.len());

    Ok(HttpResponse::Ok().json(ConvertResponse {
        name: file_name,
        title: stem,
        content: md_content,
        images: image_files,
    }))
}

// ===== 入口 =====

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenvy::dotenv().ok();
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let host = std::env::var("HOST").unwrap_or_else(|_| "127.0.0.1".into());
    let port: u16 = std::env::var("PORT")
        .unwrap_or_else(|_| "8899".into())
        .parse()
        .unwrap_or(8899);
    let mineru_api_url = std::env::var("MINERU_API_URL")
        .unwrap_or_else(|_| "https://mineru.net".into());
    let mineru_api_key =
        std::env::var("MINERU_API_KEY").unwrap_or_else(|_| String::new());
    let output_dir = std::env::var("OUTPUT_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            let mut p = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
            p.push("mineru_output");
            p
        });

    if mineru_api_key.is_empty() {
        warn!("MINERU_API_KEY 未设置，转换功能将不可用");
    }

    std::fs::create_dir_all(&output_dir).ok();
    std::fs::create_dir_all(output_dir.join("images")).ok();

    let http_client = Client::builder()
        .timeout(std::time::Duration::from_secs(300))
        .build()
        .expect("创建 HTTP 客户端失败");

    let config = AppConfig {
        mineru_api_url,
        mineru_api_key,
        output_dir: output_dir.clone(),
        http_client,
    };

    info!("MinerU 转换服务启动 → http://{}:{}", host, port);
    info!("输出目录: {:?}", output_dir);
    info!("MinerU API: {}", config.mineru_api_url);

    let data = web::Data::new(AppState {
        config: Mutex::new(config),
    });

    HttpServer::new(move || {
        App::new()
            .app_data(data.clone())
            .wrap(middleware::Logger::default())
            .service(health)
            .service(convert)
            .service(serve_image)
    })
    .bind(format!("{}:{}", host, port))?
    .run()
    .await
}
