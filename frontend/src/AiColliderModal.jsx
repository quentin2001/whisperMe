import React from 'react';

export default function AiColliderModal({
  isOpen,
  onClose,
  activeCollider,
  colliderLoading,
  colliderSynthesis,
  setColliderSynthesis,
  handleCollideSubmit
}) {
  if (!isOpen || !activeCollider) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(5, 5, 8, 0.8)',
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
        border: '1px solid var(--border-hover)',
        borderRadius: '16px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        position: 'relative'
      }}>
        {/* 关闭按钮 */}
        <button 
          onClick={onClose}
          className="btn-ghost"
          style={{ position: 'absolute', top: '16px', right: '16px', border: 'none', background: 'transparent', cursor: 'pointer', padding: '6px' }}
        >
          ✕
        </button>

        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          <h3 style={{ fontSize: '16.5px', fontWeight: '750', color: 'var(--text-primary)', margin: 0 }}>AI 强力对撞机 (The AI Collider)</h3>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>发现异界观点的隐秘联结，撞击跨界灵感火花</p>
        </div>

        {/* 卡片对比区 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', position: 'relative' }}>
          {/* 卡牌 A */}
          <div className="glass-panel" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', minHeight: '140px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '10px', color: 'var(--accent)', fontWeight: 'bold' }}>观点 A · {activeCollider.card_a.podcast_name}</div>
            <h4 style={{ fontSize: '12.5px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>{activeCollider.card_a.spark_title}</h4>
            <p style={{ fontSize: '10.5px', color: 'var(--text-secondary)', margin: 0, fontStyle: 'italic', display: '-webkit-box', WebkitLineClamp: '3', WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              "{activeCollider.card_a.quote}"
            </p>
          </div>

          {/* 卡牌 B */}
          <div className="glass-panel" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', minHeight: '140px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '10px', color: 'var(--primary)', fontWeight: 'bold' }}>观点 B · {activeCollider.card_b.podcast_name}</div>
            <h4 style={{ fontSize: '12.5px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>{activeCollider.card_b.spark_title}</h4>
            <p style={{ fontSize: '10.5px', color: 'var(--text-secondary)', margin: 0, fontStyle: 'italic', display: '-webkit-box', WebkitLineClamp: '3', WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              "{activeCollider.card_b.quote}"
            </p>
          </div>

          {/* 连线装饰 */}
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '30px',
            height: '2px',
            background: 'linear-gradient(90deg, var(--accent), var(--primary))',
            boxShadow: '0 0 10px rgba(122,162,247,0.5)',
            zIndex: 10
          }} />
        </div>

        {/* AI 对撞提问气泡 */}
        <div style={{
          background: 'var(--primary-glow)',
          border: '1px solid rgba(122, 162, 247, 0.3)',
          borderRadius: '10px',
          padding: '12px 16px',
          fontSize: '11.5px',
          color: 'var(--text-primary)',
          lineHeight: '1.5',
          textAlign: 'left'
        }}>
          <strong style={{ color: 'var(--primary)', display: 'block', marginBottom: '4px' }}>💡 AI 联想火花:</strong>
          {activeCollider.question}
        </div>

        {/* 跨界感悟输入 */}
        <form onSubmit={handleCollideSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <textarea 
            value={colliderSynthesis}
            onChange={(e) => setColliderSynthesis(e.target.value)}
            required
            placeholder="输入您的跨界顿悟（比如：这两个观点让我联想到某种共通的认知模型...）"
            className="glass-input"
            rows="3"
            style={{ width: '100%', resize: 'none', fontSize: '12px' }}
          />
          <button 
            type="submit"
            disabled={colliderLoading}
            className="btn-glow" 
            style={{ 
              padding: '10px 24px', 
              fontSize: '13px', 
              fontWeight: '700',
              background: 'linear-gradient(135deg, var(--accent), var(--primary))',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            {colliderLoading ? '正在合成...' : '💥 对撞合成'}
          </button>
        </form>
      </div>
    </div>
  );
}
