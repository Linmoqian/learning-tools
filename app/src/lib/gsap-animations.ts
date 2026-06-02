import { useEffect, useRef, useCallback, RefObject } from 'react';
import gsap from 'gsap';

// ===== 共享默认配置 =====
gsap.defaults({
  ease: 'power2.out',
  duration: 0.5,
});

// ===== Hook: 交错入场 =====
export function useStaggerEntrance(deps: any[] = []) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const items = el.children;
    if (!items.length) return;

    gsap.fromTo(
      items,
      { y: 30, opacity: 0, scale: 0.95 },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        duration: 0.5,
        ease: 'back.out(1.7)',
        stagger: { each: 0.06, from: 'start' },
      },
    );
  }, deps);

  return ref;
}

// ===== Hook: 子元素弹性交错入场（指定根 ref） =====
export function useStaggerChildren(
  rootRef: RefObject<HTMLElement | null>,
  options?: { from?: 'start' | 'center' | 'end' | 'random'; each?: number },
) {
  const animate = useCallback(() => {
    const el = rootRef.current;
    if (!el) return;
    const children = el.children;
    if (!children.length) return;

    gsap.fromTo(
      children,
      { y: 24, opacity: 0, scale: 0.9 },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        duration: 0.45,
        ease: 'back.out(1.7)',
        stagger: { each: options?.each ?? 0.07, from: options?.from ?? 'start' },
      },
    );
  }, [rootRef, options]);

  return animate;
}

// ===== Hook: 呼吸脉冲 =====
export function usePulse(ref: RefObject<HTMLElement | null>, intensity = 1) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const tl = gsap.timeline({ repeat: -1, yoyo: true });
    tl.to(el, {
      scale: 1 + 0.03 * intensity,
      duration: 1.5 + 0.5 * (1 - intensity),
      ease: 'sine.inOut',
    });

    return () => { tl.kill(); };
  }, [ref, intensity]);
}

// ===== Hook: 弹性悬浮 =====
export function useHoverFloat(ref: RefObject<HTMLElement | null>) {
  const tlRef = useRef<gsap.core.Tween | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const onEnter = () => {
      tlRef.current?.kill();
      tlRef.current = gsap.to(el, {
        y: -4,
        scale: 1.04,
        duration: 0.35,
        ease: 'back.out(2)',
      });
    };

    const onLeave = () => {
      tlRef.current?.kill();
      tlRef.current = gsap.to(el, {
        y: 0,
        scale: 1,
        duration: 0.4,
        ease: 'elastic.out(1, 0.3)',
      });
    };

    el.addEventListener('mouseenter', onEnter);
    el.addEventListener('mouseleave', onLeave);

    return () => {
      el.removeEventListener('mouseenter', onEnter);
      el.removeEventListener('mouseleave', onLeave);
      tlRef.current?.kill();
    };
  }, [ref]);
}

// ===== Hook: 弹性点击反馈 =====
export function useTapBounce(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const onDown = () => {
      gsap.to(el, { scale: 0.92, duration: 0.1, ease: 'none' });
    };
    const onUp = () => {
      gsap.to(el, { scale: 1, duration: 0.3, ease: 'elastic.out(1, 0.2)' });
    };

    el.addEventListener('mousedown', onDown);
    el.addEventListener('mouseup', onUp);
    el.addEventListener('mouseleave', onUp);

    return () => {
      el.removeEventListener('mousedown', onDown);
      el.removeEventListener('mouseup', onUp);
      el.removeEventListener('mouseleave', onUp);
    };
  }, [ref]);
}

// ===== Hook: 页面标题入场 =====
export function usePageEntrance(deps: any[] = []) {
  const titleRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline();

    if (titleRef.current) {
      tl.fromTo(
        titleRef.current,
        { y: -20, opacity: 0, scale: 0.95 },
        { y: 0, opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.7)' },
      );
    }

    if (contentRef.current) {
      const children = contentRef.current.children;
      if (children.length) {
        tl.fromTo(
          children,
          { y: 20, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.4,
            ease: 'power2.out',
            stagger: 0.08,
          },
          '-=0.1',
        );
      }
    }

    return () => { tl.kill(); };
  }, deps);

  return { titleRef, contentRef };
}

// ===== Hook: 抖动动画 =====
export function useShake(ref: RefObject<HTMLElement | null>, trigger: any) {
  useEffect(() => {
    if (!trigger) return;
    const el = ref.current;
    if (!el) return;

    const tl = gsap.timeline();
    tl.to(el, { x: -8, duration: 0.07 })
      .to(el, { x: 8, duration: 0.07 })
      .to(el, { x: -6, duration: 0.06 })
      .to(el, { x: 6, duration: 0.06 })
      .to(el, { x: -3, duration: 0.05 })
      .to(el, { x: 3, duration: 0.05 })
      .to(el, { x: 0, duration: 0.09, ease: 'power2.out' });
    return () => { tl.kill(); };
  }, [ref, trigger]);
}
