import React, { useState, useEffect } from 'react';

export default function AiColliderModal({
  isOpen,
  onClose,
  activeCollider,
  colliderLoading,
  colliderSynthesis,
  setColliderSynthesis,
  handleCollideSubmit
}) {
  if (!isOpen) return null;

  const [scanStep, setScanStep] = useState(0); // 0: idle, 1: accel, 2: search, 3: lock, 4: complete

  useEffect(() => {
    if (isOpen) {
      if (colliderLoading) {
        setScanStep(1); // Accel/Loading
      } else if (activeCollider) {
        // Run scanning animation sequence
        setScanStep(2); // Scanning entropy
        const t1 = setTimeout(() => setScanStep(3), 1000); // Locking resonance
        const t2 = setTimeout(() => setScanStep(4), 2000); // Revealed
        return () => {
          clearTimeout(t1);
          clearTimeout(t2);
        };
      }
    } else {
      setScanStep(0);
    }
  }, [isOpen, colliderLoading, activeCollider]);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(5, 5, 8, 0.85)',
      backdropFilter: 'blur(15px)',
      WebkitBackdropFilter: 'blur(15px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '740px',
        padding: '28px',
        background: 'var(--bg-surface)',
        border: '2px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(122, 162, 247, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Glow overlay */}
        <div style={{
          position: 'absolute',
          top: '-150px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(122,162,247,0.15) 0%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0
        }} />

        {/* 关闭按钮 */}
        <button 
          onClick={onClose}
          className="btn-ghost"
          style={{ position: 'absolute', top: '16px', right: '16px', border: 'none', background: 'transparent', cursor: 'pointer', padding: '6px', zIndex: 10 }}
        >
          ✕
        </button>

        {/* ── SCREEN A: SCANNING COLLIDER SIMULATOR ── */}
        {scanStep < 4 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '340px', gap: '28px', zIndex: 1 }}>
            {/* Spinning accelerator graphic */}
            <div style={{ position: 'relative', width: '100px', height: '100px' }}>
              {/* Outer ring */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                border: '3px dashed var(--accent)',
                animation: 'spin 4s linear infinite',
                boxShadow: '0 0 15px rgba(239, 68, 68, 0.2)'
              }} />
              {/* Inner opposite ring */}
              <div style={{
                position: 'absolute',
                top: '10px',
                left: '10px',
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                border: '3px dashed var(--primary)',
                animation: 'spin 2s linear infinite reverse',
                boxShadow: '0 0 15px rgba(122, 162, 247, 0.2)'
              }} />
              {/* Core pulsing particle */}
              <div style={{
                position: 'absolute',
                top: '35px',
                left: '35px',
                width: '30px',
                height: '30px',
                borderRadius: '50%',
                background: 'radial-gradient(circle, #ffffff 20%, var(--accent) 70%, var(--primary) 100%)',
                animation: 'pulse-neon 0.6s infinite alternate',
                boxShadow: '0 0 20px var(--accent)'
              }} />
            </div>

            {/* Scan Steps Text */}
            <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <h4 style={{ fontSize: '15px', fontWeight: '800', color: 'var(--text-primary)', margin: 0, letterSpacing: '1px' }}>
                {scanStep === 1 && '📡 脑电粒子加速器启动中...'}
                {scanStep === 2 && '🔍 正在检索跨领域脑洞关联熵...'}
                {scanStep === 3 && '💥 捕捉到高张力脑电对撞信号！'}
              </h4>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
                {scanStep === 1 && '激发相干性粒子，准备探测思维场...'}
                {scanStep === 2 && '检索沙盒卡片库，度量不同维度的张力同构...'}
                {scanStep === 3 && '对撞锁定成功，正在重构量子认知连线...'}
              </p>
            </div>

            {/* Scanning Progress Bar */}
            <div style={{ width: '240px', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                background: 'linear-gradient(90deg, var(--accent), var(--primary))',
                width: scanStep === 1 ? '30%' : scanStep === 2 ? '65%' : '90%',
                transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: '0 0 8px var(--primary)'
              }} />
            </div>
          </div>
        ) : (
          // ── SCREEN B: REVEALED COLLISION PAIR & SYNTHESIS FORM ──
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', zIndex: 1 }}>
            {/* Header */}
            <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px', filter: 'drop-shadow(0 0 4px #ffd700)' }}>💥</span>
                <h3 style={{ fontSize: '17px', fontWeight: '800', color: 'var(--text-primary)', margin: 0, letterSpacing: '1px' }}>
                  跨界灵感对撞机
                </h3>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: 0 }}>
                自动搜寻无关联卡片 · 探索哲理深处的共鸣火花
              </p>
            </div>

            {/* Tension Indicator */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              background: 'rgba(212, 175, 55, 0.08)',
              border: '1px solid rgba(212, 175, 55, 0.2)',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '12px',
              color: '#ffd700',
              fontWeight: '800'
            }}>
              <span>⚡ 思想张力指数: {activeCollider.dissonance_index || 88}%</span>
              <span style={{ color: 'var(--text-muted)', fontWeight: '400' }}>|</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '11px', fontWeight: '500' }}>
                {activeCollider.dissonance_index >= 90 ? '🔥 异界深层共振 (极高跨度)' : '💡 强共鸣相似度'}
              </span>
            </div>

            {/* Side-by-side collision cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', position: 'relative' }}>
              {/* Card A */}
              <div className="glass-panel" style={{
                padding: '16px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '12px',
                minHeight: '140px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ fontSize: '10px', color: '#f87171', fontWeight: 'bold' }}>
                  观点 A · {activeCollider.card_a.podcast_name}
                </div>
                <h4 style={{ fontSize: '12px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
                  {activeCollider.card_a.spark_title}
                </h4>
                <p style={{
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  fontStyle: 'italic',
                  lineHeight: '1.45',
                  display: '-webkit-box',
                  WebkitLineClamp: '4',
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  "{activeCollider.card_a.quote}"
                </p>
              </div>

              {/* Card B */}
              <div className="glass-panel" style={{
                padding: '16px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(122, 162, 247, 0.25)',
                borderRadius: '12px',
                minHeight: '140px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ fontSize: '10px', color: '#93c5fd', fontWeight: 'bold' }}>
                  观点 B · {activeCollider.card_b.podcast_name}
                </div>
                <h4 style={{ fontSize: '12px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
                  {activeCollider.card_b.spark_title}
                </h4>
                <p style={{
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  fontStyle: 'italic',
                  lineHeight: '1.45',
                  display: '-webkit-box',
                  WebkitLineClamp: '4',
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  "{activeCollider.card_b.quote}"
                </p>
              </div>

              {/* Central Collision Decorator */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: 'var(--bg-surface)',
                border: '2px solid #ffd700',
                boxShadow: '0 0 10px #ffd700',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                zIndex: 10
              }}>
                💥
              </div>
            </div>

            {/* Dissonance Matching Reason */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '12px 16px',
              fontSize: '11.5px',
              color: 'var(--text-secondary)',
              lineHeight: '1.5',
              textAlign: 'left'
            }}>
              <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '2px' }}>📡 对撞引力波理由:</strong>
              {activeCollider.match_reason}
            </div>

            {/* Prompted Question from LLM */}
            <div style={{
              background: 'var(--primary-glow)',
              border: '1px solid rgba(122, 162, 247, 0.3)',
              borderRadius: '10px',
              padding: '12px 16px',
              fontSize: '12px',
              color: 'var(--text-primary)',
              lineHeight: '1.5',
              textAlign: 'left',
              boxShadow: 'inset 0 0 15px rgba(122,162,247,0.05)'
            }}>
              <strong style={{ color: 'var(--primary)', display: 'block', marginBottom: '4px' }}>💡 对撞启发发问:</strong>
              {activeCollider.question}
            </div>

            {/* Synthesis Form */}
            <form onSubmit={handleCollideSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <textarea 
                value={colliderSynthesis}
                onChange={(e) => setColliderSynthesis(e.target.value)}
                required
                placeholder="在此输入您的融合思考与顿悟（合成后将基于您的感悟与两个母观点，由 AI 融铸提炼出一张全新的【合题灵感卡片】沉淀在沙盒中）"
                className="glass-input"
                rows="3"
                style={{ width: '100%', resize: 'none', fontSize: '12px', padding: '10px 12px' }}
              />
              <button 
                type="submit"
                className="btn-glow" 
                style={{ 
                  padding: '10px 24px', 
                  fontSize: '13px', 
                  fontWeight: '700',
                  background: 'linear-gradient(135deg, var(--accent), var(--primary))',
                  border: 'none',
                  cursor: 'pointer',
                  borderRadius: '6px',
                  color: '#fff',
                  boxShadow: '0 4px 12px rgba(122, 162, 247, 0.3)'
                }}
              >
                💥 合成灵感合题
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
