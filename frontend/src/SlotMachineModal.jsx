import React from 'react';

export default function SlotMachineModal({
  isOpen,
  onClose,
  isSpinning,
  spinReelsResolved,
  dueCards,
  reviewedCardIds,
  forgottenCardIds,
  leverActive,
  triggerLeverPull,
  handleReviewCard,
  handleSpinSlotMachine
}) {
  if (!isOpen) return null;

  // Custom SVG Symbol Renderers for reels & paytables (No Emojis)
  const ReelSymbols = {
    cherry: (style = {}) => (
      <svg width="40" height="40" viewBox="0 0 40 40" style={style}>
        <circle cx="14" cy="27" r="7" fill="#dc2626" />
        <circle cx="26" cy="24" r="7" fill="#dc2626" />
        <path d="M 14 20 C 14 11 24 9 24 9 M 26 17 C 26 11 24 9 24 9" stroke="#16a34a" strokeWidth="2.5" fill="none" />
        <rect x="22" y="6" width="4" height="4" fill="#16a34a" transform="rotate(15 22 6)" />
      </svg>
    ),
    bell: (style = {}) => (
      <svg width="40" height="40" viewBox="0 0 40 40" style={style}>
        <path d="M 20 6 C 13 6 11 15 11 24 L 29 24 C 29 15 27 6 20 6 Z" fill="#eab308" stroke="#a16207" strokeWidth="1.5" />
        <rect x="9" y="24" width="22" height="3" rx="1.5" fill="#ca8a04" stroke="#a16207" strokeWidth="1" />
        <circle cx="20" cy="29" r="2.5" fill="#ca8a04" />
      </svg>
    ),
    seven: (style = {}) => (
      <svg width="32" height="38" viewBox="0 0 32 38" style={style}>
        <path d="M 4 4 L 28 4 L 14 34 L 6 34 L 20 8 L 4 8 Z" fill="#e11d48" stroke="#9f1239" strokeWidth="1" />
      </svg>
    ),
    bar: (style = {}) => (
      <div style={{
        background: '#000000',
        border: '2.5px double #ffffff',
        borderRadius: '4px',
        padding: '3px 6px',
        color: '#ffffff',
        fontFamily: "'Impact', 'Arial Black', sans-serif",
        fontSize: '12px',
        fontWeight: '900',
        letterSpacing: '1px',
        textAlign: 'center',
        width: '50px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
        textTransform: 'uppercase',
        display: 'inline-block',
        userSelect: 'none',
        ...style
      }}>
        BAR
      </div>
    )
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(5, 5, 8, 0.85)',
      backdropFilter: 'blur(8px)',
      WebkitBackdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      overflowY: 'auto',
      padding: '40px 0'
    }}>
      {/* 关闭返回按钮 */}
      <button 
        onClick={onClose}
        className="slot-btn-glossy btn-blue"
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          width: '90px',
          height: '46px',
          borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.5)',
          zIndex: 2002,
          cursor: 'pointer',
          fontSize: '12px'
        }}
      >
        返回
      </button>

      {/* Centered JUMBO Slot Machine Cabinet */}
      <div 
        className="slot-cabinet" 
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          position: 'relative',
          marginRight: '60px',
          overflow: 'visible',
          width: '460px',
          maxHeight: 'calc(100vh - 80px)',
          overflowY: 'visible'
        }}
      >
        {/* Top Siren Dome Light */}
        <div className={`slot-siren ${isSpinning ? 'flashing' : ''}`} onClick={triggerLeverPull} />

        {/* Arched Top Header like JUMBO SLOT */}
        <div className="slot-header-arch">
          <h3 className="slot-arch-title">Jumbo Slot</h3>
          <h4 className="slot-arch-subtitle">Savings Bank</h4>
        </div>

        {/* Top Paytable Display Board */}
        <div className="slot-paytable-board">
          <div className="paytable-col">
            <div className="paytable-row">
              <div className="paytable-icons">
                {ReelSymbols.seven({ transform: 'scale(0.5)', transformOrigin: 'left center', width: '16px', height: '20px' })}
                {ReelSymbols.seven({ transform: 'scale(0.5)', transformOrigin: 'left center', width: '16px', height: '20px' })}
                {ReelSymbols.seven({ transform: 'scale(0.5)', transformOrigin: 'left center', width: '16px', height: '20px' })}
              </div>
              <span className="paytable-payout">150</span>
            </div>
            <div className="paytable-row">
              <div className="paytable-icons">
                {ReelSymbols.bell({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '18px', height: '18px' })}
                {ReelSymbols.bell({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '18px', height: '18px' })}
                {ReelSymbols.bell({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '18px', height: '18px' })}
              </div>
              <span className="paytable-payout">80</span>
            </div>
          </div>

          <div className="paytable-coins-graphic">
            <div style={{ display: 'flex', gap: '2.5px', flexWrap: 'wrap', justifyContent: 'center', maxWidth: '42px', opacity: 0.85 }}>
              <div className="gold-coin" style={{ width: '9px', height: '9px' }} />
              <div className="gold-coin" style={{ width: '9px', height: '9px' }} />
              <div className="gold-coin" style={{ width: '9px', height: '9px' }} />
              <div className="gold-coin" style={{ width: '9px', height: '9px' }} />
              <div className="gold-coin" style={{ width: '9px', height: '9px' }} />
            </div>
            <span style={{ fontSize: '7px', color: '#ffd700', fontWeight: '900', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.5px', fontFamily: 'Impact, sans-serif' }}>Jackpot</span>
          </div>

          <div className="paytable-col">
            <div className="paytable-row">
              <div className="paytable-icons">
                {ReelSymbols.bar({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '30px', fontSize: '9px', padding: '1px 3px' })}
                {ReelSymbols.bar({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '30px', fontSize: '9px', padding: '1px 3px' })}
                {ReelSymbols.bar({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '30px', fontSize: '9px', padding: '1px 3px' })}
              </div>
              <span className="paytable-payout">100</span>
            </div>
            <div className="paytable-row">
              <div className="paytable-icons">
                {ReelSymbols.cherry({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '18px', height: '18px' })}
                {ReelSymbols.cherry({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '18px', height: '18px' })}
                {ReelSymbols.cherry({ transform: 'scale(0.55)', transformOrigin: 'left center', width: '18px', height: '18px' })}
              </div>
              <span className="paytable-payout">50</span>
            </div>
          </div>
        </div>

        {/* Center Bezel and Reels Screen */}
        <div style={{ 
          position: 'relative', 
          padding: '24px 20px', 
          background: 'rgba(5, 5, 8, 0.95)', 
          borderRadius: '16px', 
          border: '3px solid var(--border-color)', 
          boxShadow: '0 0 15px rgba(255, 255, 255, 0.05), inset 0 0 25px rgba(0, 0, 0, 0.95)' 
        }}>
          {/* Blinking Bulbs around the bezel (top) */}
          <div style={{ position: 'absolute', top: '7px', left: '16px', right: '16px', display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
            {[...Array(11)].map((_, i) => (
              <div key={i} className={`slot-bulb ${i % 2 === 0 ? 'slot-bulb-odd' : 'slot-bulb-even'}`} />
            ))}
          </div>
          
          {/* Blinking Bulbs around the bezel (bottom) */}
          <div style={{ position: 'absolute', bottom: '7px', left: '16px', right: '16px', display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
            {[...Array(11)].map((_, i) => (
              <div key={i} className={`slot-bulb ${i % 2 === 1 ? 'slot-bulb-odd' : 'slot-bulb-even'}`} />
            ))}
          </div>

          {/* 3 reels screen container */}
          <div className="reel-container" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
            gap: '16px',
            padding: '12px',
            minHeight: '240px',
            position: 'relative'
          }}>
            {/* Red Payline Line - Absolute positioned inline to not affect grid flow */}
            <div style={{
              position: 'absolute',
              top: '50%',
              left: 0,
              right: 0,
              height: '2px',
              background: 'rgba(239, 68, 68, 0.65)',
              boxShadow: '0 0 6px rgba(239, 68, 68, 0.8)',
              zIndex: 8,
              pointerEvents: 'none'
            }} />

            {/* Semi-reflective glass overlay - Absolute positioned inline to not affect grid flow */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              background: 'linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.04) 30%, transparent 50%, rgba(0,0,0,0.1) 80%, rgba(0,0,0,0.3) 100%)',
              pointerEvents: 'none',
              zIndex: 7,
              borderRadius: '8px'
            }} />

            {[0, 1, 2].map((idx) => {
              const isResolved = spinReelsResolved[idx];
              const card = dueCards[idx];
              const isReviewed = card && reviewedCardIds.has(card.id);
              const isForgotten = card && forgottenCardIds.has(card.id);

              // 1. 如果正在旋转，或者是未决状态（正在等待该滚轮停下）
              if (isSpinning && !isResolved) {
                return (
                  <div 
                    key={idx} 
                    className="paper-reel-strip" 
                    style={{ 
                      height: '240px', 
                      borderRadius: '12px',
                      overflow: 'hidden',
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      minWidth: 0
                    }}
                  >
                    {/* 滚动的仿真纸带 */}
                    <div className="reel-spinning-strip" style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '24px',
                      alignItems: 'center',
                      filter: 'blur(2px)'
                    }}>
                      {ReelSymbols.seven()}
                      {ReelSymbols.bell()}
                      {ReelSymbols.cherry()}
                      {ReelSymbols.bar()}
                      {ReelSymbols.seven()}
                      {ReelSymbols.bell()}
                      {ReelSymbols.cherry()}
                      {ReelSymbols.bar()}
                    </div>
                  </div>
                );
              }

              // 2. 如果已停止且该位置存在卡片
              if (isResolved && card) {
                // Slot index mappings to symbols
                const matchingSymbol = idx === 0 
                  ? ReelSymbols.seven({ position: 'absolute', top: '10px', right: '10px', transform: 'scale(0.65)', transformOrigin: 'top right' }) 
                  : idx === 1 
                    ? ReelSymbols.bell({ position: 'absolute', top: '8px', right: '8px', transform: 'scale(0.65)', transformOrigin: 'top right' }) 
                    : ReelSymbols.cherry({ position: 'absolute', top: '8px', right: '8px', transform: 'scale(0.65)', transformOrigin: 'top right' });

                return (
                  <div 
                    key={idx} 
                    className={`paper-reel-strip reel-stop-bounce ${isForgotten ? 'flame-effect' : ''}`} 
                    style={{ 
                      height: '240px', 
                      borderRadius: '12px',
                      display: 'flex', 
                      flexDirection: 'column', 
                      justifyContent: 'space-between',
                      padding: '16px',
                      background: '#ffffff', // Force white paper background
                      color: '#111111', // Force dark readable text
                      borderLeft: '1px solid #ddd',
                      borderRight: '1px solid #ddd',
                      borderTop: '2px solid #ccc',
                      borderBottom: '2px solid #ccc',
                      opacity: isReviewed && !isForgotten ? 0.65 : 1,
                      transform: isReviewed && !isForgotten ? 'scale(0.97)' : 'scale(1)',
                      transition: 'opacity 0.4s, transform 0.4s',
                      position: 'relative',
                      boxShadow: 'inset 0 10px 10px -5px rgba(0,0,0,0.15), inset 0 -10px 10px -5px rgba(0,0,0,0.15)',
                      minWidth: 0
                    }}
                  >
                    {/* 封面、来源和标题 */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {card.podcast_image_url ? (
                          <img src={card.podcast_image_url} alt="cover" style={{ width: '18px', height: '18px', borderRadius: '4px', objectFit: 'cover', border: '1px solid #ccc' }} />
                        ) : (
                          <span style={{ fontSize: '14px' }}>🎙️</span>
                        )}
                        <span style={{ fontSize: '10px', color: '#555555', fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '60px' }}>{card.podcast_name}</span>
                      </div>
                      <h4 style={{ fontSize: '12px', fontWeight: '800', color: '#111111', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '22px' }}>{card.spark_title}</h4>
                      <p style={{ 
                        fontSize: '10px', 
                        color: '#333333', 
                        margin: 0,
                        lineHeight: '1.4',
                        display: '-webkit-box',
                        WebkitLineClamp: '4',
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        fontStyle: 'italic',
                        borderLeft: '2.5px solid #d4af37', // Gold paper edge accent
                        paddingLeft: '6px'
                      }}>
                        "{card.quote}"
                      </p>
                    </div>

                    {/* Absolute Positioned SVG Reel Symbol Badge on the Paper */}
                    {matchingSymbol}

                    {/* 命运滑块或操作Badge */}
                    <div>
                      {!isReviewed ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '10px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#666666', fontWeight: '700' }}>
                            <span>👈 我已驯服</span>
                            <span>忘了 👉</span>
                          </div>
                          <input 
                            type="range"
                            min="-100"
                            max="100"
                            defaultValue="0"
                            className="glass-slider"
                            style={{ width: '100%', cursor: 'ew-resize', accentColor: '#d4af37' }}
                            onMouseUp={(e) => {
                              const val = parseInt(e.target.value);
                              if (val <= -70) {
                                handleReviewCard(card.id, 'left');
                              } else if (val >= 70) {
                                handleReviewCard(card.id, 'right');
                              } else {
                                e.target.value = 0;
                              }
                            }}
                            onTouchEnd={(e) => {
                              const val = parseInt(e.target.value);
                              if (val <= -70) {
                                handleReviewCard(card.id, 'left');
                              } else if (val >= 70) {
                                handleReviewCard(card.id, 'right');
                              } else {
                                e.target.value = 0;
                              }
                            }}
                          />
                        </div>
                      ) : (
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'center', 
                          alignItems: 'center', 
                          padding: '5px 8px', 
                          borderRadius: '6px',
                          background: isForgotten ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                          color: isForgotten ? '#dc2626' : '#059669',
                          fontSize: '10px',
                          fontWeight: '800',
                          marginTop: '10px',
                          border: isForgotten ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid rgba(16, 185, 129, 0.25)',
                        }}>
                          {isForgotten ? '🔥 遗忘，稍后复习' : '✅ 已驯服'}
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              // 3. 初始或空状态 (Idle)
              return (
                <div 
                  key={idx} 
                  className="paper-reel-strip" 
                  style={{ 
                    height: '240px', 
                    borderRadius: '12px',
                    display: 'flex', 
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    color: '#bbb',
                    borderStyle: 'dashed',
                    borderWidth: '2px',
                    borderColor: '#bbb',
                    position: 'relative',
                    minWidth: 0
                  }}
                >
                  {idx === 0 ? ReelSymbols.seven({ opacity: 0.15, transform: 'scale(1.2)' }) : idx === 1 ? ReelSymbols.bell({ opacity: 0.15, transform: 'scale(1.2)' }) : ReelSymbols.cherry({ opacity: 0.15, transform: 'scale(1.2)' })}
                  <span style={{ fontSize: '10px', marginTop: '12px', fontWeight: '900', color: '#999', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Reel {idx + 1} Ready</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 底部黑色豪华奖励规则牌 (Lower Prize Board) */}
        <div className="slot-lower-panel">
          <h4 className="slot-lower-title">Bars & Sevens Wins!</h4>
          <div className="slot-lower-combos">
            <div className="slot-lower-box">
              {ReelSymbols.bar({ transform: 'scale(0.8)', transformOrigin: 'center center', width: '42px', fontSize: '9px', padding: '1px 2px' })}
              {ReelSymbols.seven({ transform: 'scale(0.6)', width: '20px', height: '24px' })}
              {ReelSymbols.bar({ transform: 'scale(0.8)', transformOrigin: 'center center', width: '42px', fontSize: '9px', padding: '1px 2px' })}
            </div>
            <div style={{ color: '#ffd700', fontSize: '10px', fontWeight: '900', fontFamily: 'Impact, sans-serif' }}>OR</div>
            <div className="slot-lower-box">
              {ReelSymbols.seven({ transform: 'scale(0.6)', width: '20px', height: '24px' })}
              {ReelSymbols.seven({ transform: 'scale(0.6)', width: '20px', height: '24px' })}
              {ReelSymbols.seven({ transform: 'scale(0.6)', width: '20px', height: '24px' })}
            </div>
          </div>
        </div>

        {/* Control Deck with 3D Glossy Buttons and Coin Slot */}
        <div className="slot-deck">
          <button 
            onClick={triggerLeverPull}
            disabled={isSpinning}
            className="slot-btn-glossy"
            style={{ outline: 'none' }}
          >
            <span style={{ fontSize: '11px', fontWeight: 'bold' }}>SPIN</span>
          </button>

          <div className="coin-slot" title="COGNITIVE COIN SLOT">
            <span className="coin-slot-label">1 play</span>
          </div>

          <button 
            onClick={handleSpinSlotMachine}
            disabled={isSpinning}
            className="slot-btn-glossy btn-blue"
            style={{ outline: 'none' }}
          >
            <span style={{ fontSize: '11px', fontWeight: 'bold' }}>AUTO</span>
          </button>
        </div>

        {/* Payout Coin Tray at base with stacked physical golden coins */}
        <div className="slot-tray">
          <div className="slot-tray-label">Payout Tray</div>
          <div className="coin-pile">
            <div className="gold-coin" />
            <div className="gold-coin" />
            <div className="gold-coin" />
            <div className="gold-coin" />
            <div className="gold-coin" />
            <div className="gold-coin" />
            <div className="gold-coin" />
            <div className="gold-coin" />
          </div>
        </div>

        {/* Right: The Physical 3D Lever (Sticks out of the cabinet side) */}
        <div 
          onClick={triggerLeverPull}
          style={{
            width: '60px',
            height: '220px',
            position: 'absolute',
            right: '-52px',
            top: '130px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'flex-end',
            cursor: isSpinning ? 'not-allowed' : 'pointer',
            userSelect: 'none',
            zIndex: 10
          }}
        >
          {/* Side Mount Chrome Bracket */}
          <div style={{
            width: '24px',
            height: '40px',
            background: 'linear-gradient(90deg, #333 0%, #aaa 50%, #222 100%)',
            border: '2px solid #555',
            borderRadius: '4px',
            position: 'absolute',
            bottom: '20px',
            left: '18px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.6)'
          }} />
          
          {/* Lever Rod (The Metal Pole) */}
          <div style={{
            width: '8px',
            height: '110px',
            background: 'linear-gradient(90deg, #888 0%, #fff 50%, #555 100%)',
            borderRadius: '4px',
            position: 'absolute',
            bottom: '40px',
            left: '26px',
            transformOrigin: 'bottom center',
            transform: leverActive ? 'rotateX(75deg) scaleY(0.4) translateY(45px)' : 'rotateX(0deg) scaleY(1) translateY(0)',
            transition: 'transform 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
            zIndex: 2,
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
          }}>
            {/* Red Glossy Ball Handle */}
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'radial-gradient(circle at 10px 10px, #ff4d4d, #990000 60%, #4a0000 100%)',
              position: 'absolute',
              top: '-26px',
              left: '-12px',
              boxShadow: isSpinning ? '0 0 14px #ff4d4d' : '0 6px 12px rgba(0,0,0,0.4)',
              border: '1px solid rgba(255,255,255,0.2)'
            }} />
          </div>
        </div>
      </div>
    </div>
  );
}
