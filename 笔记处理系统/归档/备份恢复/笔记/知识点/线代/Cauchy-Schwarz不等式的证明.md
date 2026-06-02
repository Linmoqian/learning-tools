# Cauchy-Schwarz不等式的证明（判别式法）

> 📖 来源：[[../../线代/05_向量运算与内积|05_向量运算与内积]]

## 定义
Cauchy-Schwarz不等式的经典证明方法：构造关于t的二次函数 $f(t)=\langle\alpha+t\beta,\alpha+t\beta\rangle$，利用内积正定性知 $f(t)\geq 0$ 恒成立，由判别式 $\Delta \leq 0$ 即得不等式。此证法对任意维数均成立。

## 公式
构造 $f(t) = \|\alpha\|^2 + 2t\langle\alpha,\beta\rangle + t^2\|\beta\|^2 \geq 0$

判别式：$\Delta = 4\langle\alpha,\beta\rangle^2 - 4\|\alpha\|^2\|\beta\|^2 \leq 0$

$$ \Rightarrow |\langle \alpha, \beta \rangle| \leq \|\alpha\| \cdot \|\beta\| $$

## 通俗理解
> 把一个几何不等式转化为一个二次函数恒非负的问题——就像证明"抛物线不会掉到x轴以下"，只要判别式≤0就行。这是一种"化几何为代数"的经典技巧。

## 🔗 关联

- [[内积]]
- [[模的四大性质]]
- 三角不等式
- 二次判别式







