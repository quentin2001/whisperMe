import React, { useState } from 'react';

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
  handleSpinSlotMachine,
  slotTheme,
  setSlotTheme
}) {
  if (!isOpen) return null;

  // Local fallback theme states in case props are not passed
  const [localTheme, setLocalTheme] = useState('gold');
  const activeTheme = slotTheme || localTheme;
  const activeSetTheme = setSlotTheme || setLocalTheme;

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

  // Golden Theme High Fidelity Symbol Renderers
  const GoldReelSymbols = {
    seven: (style = {}) => (
      <svg width="40" height="50" viewBox="0 0 32 38" style={{ filter: 'drop-shadow(0px 3px 3px rgba(0,0,0,0.6))', ...style }}>
        <path d="M 4 4 L 28 4 L 14 34 L 6 34 L 20 8 L 4 8 Z" fill="#ef4444" stroke="#4a0005" strokeWidth="2.5" strokeLinejoin="round" />
      </svg>
    ),
    cherry: (style = {}) => (
      <svg width="40" height="40" viewBox="0 0 40 40" style={{ filter: 'drop-shadow(0px 2px 3px rgba(0,0,0,0.6))', ...style }}>
        <circle cx="13" cy="27" r="8" fill="#ef4444" stroke="#4a0005" strokeWidth="2" />
        <circle cx="27" cy="23" r="8" fill="#ef4444" stroke="#4a0005" strokeWidth="2" />
        <path d="M 13 19 C 13 9 25 7 25 7 M 27 15 C 27 9 25 7 25 7" stroke="#22c55e" strokeWidth="3" fill="none" strokeLinecap="round" />
        <rect x="23" y="4" width="5" height="5" fill="#22c55e" stroke="#14532d" strokeWidth="1" transform="rotate(15 23 4)" />
      </svg>
    ),
    bell: (style = {}) => (
      <svg width="40" height="40" viewBox="0 0 40 40" style={{ filter: 'drop-shadow(0px 2px 3px rgba(0,0,0,0.6))', ...style }}>
        <path d="M 20 5 C 12 5 10 15 10 25 L 30 25 C 30 15 28 5 20 5 Z" fill="#fbbf24" stroke="#78350f" strokeWidth="2" strokeLinejoin="round" />
        <rect x="7" y="25" width="26" height="4" rx="2" fill="#d97706" stroke="#78350f" strokeWidth="1.5" />
        <circle cx="20" cy="31" r="3.5" fill="#b45309" stroke="#78350f" strokeWidth="1" />
      </svg>
    ),
    bar: (style = {}) => (
      <div style={{
        background: 'linear-gradient(180deg, #111 0%, #222 40%, #000 100%)',
        border: '3px solid #facc15',
        borderRadius: '6px',
        padding: '5px 10px',
        color: '#facc15',
        fontFamily: "'Impact', 'Arial Black', sans-serif",
        fontSize: '13px',
        fontWeight: '900',
        letterSpacing: '1.5px',
        textAlign: 'center',
        width: '60px',
        boxShadow: '0 3px 6px rgba(0,0,0,0.6), inset 0 1px 2px rgba(255,255,255,0.4)',
        textTransform: 'uppercase',
        display: 'inline-block',
        userSelect: 'none',
        textShadow: '0 2px 4px rgba(0,0,0,0.8)',
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
      background: 'rgba(5, 5, 8, 0.88)',
      backdropFilter: 'blur(10px)',
      WebkitBackdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      overflowY: 'auto',
      padding: '40px 0'
    }}>
      {/* Theme Toggles at top-left/center */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        display: 'flex',
        gap: '12px',
        zIndex: 2002
      }}>
        <button
          onClick={() => activeSetTheme('jumbo')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'all 0.2s',
            border: activeTheme === 'jumbo' ? '2px solid var(--primary)' : '1px solid var(--border-color)',
            background: activeTheme === 'jumbo' ? 'var(--primary-glow)' : 'rgba(255,255,255,0.05)',
            color: activeTheme === 'jumbo' ? 'var(--primary)' : 'var(--text-secondary)'
          }}
        >
          经典复古款 (Jumbo)
        </button>
        <button
          onClick={() => activeSetTheme('gold')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'all 0.2s',
            border: activeTheme === 'gold' ? '2px solid #ffd700' : '1px solid var(--border-color)',
            background: activeTheme === 'gold' ? 'rgba(212, 175, 55, 0.15)' : 'rgba(255,255,255,0.05)',
            color: activeTheme === 'gold' ? '#ffd700' : 'var(--text-secondary)',
            boxShadow: activeTheme === 'gold' ? '0 0 10px rgba(212, 175, 55, 0.3)' : 'none'
          }}
        >
          奢华黄金款 (Golden 3D)
        </button>
      </div>

      {/* Close/Back Button */}
      <button 
        onClick={onClose}
        className="slot-btn-glossy btn-blue"
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          width: '90px',
          height: '40px',
          borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.5)',
          zIndex: 2002,
          cursor: 'pointer',
          fontSize: '12px'
        }}
      >
        返回
      </button>

      {/* Render JUMBO Retro Slot Machine */}
      {activeTheme === 'jumbo' && (
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
              {/* Red Payline Line */}
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

              {/* Semi-reflective glass overlay */}
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

                if (isResolved && card) {
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
                        background: '#ffffff',
                        color: '#111111',
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
                          borderLeft: '2.5px solid #d4af37',
                          paddingLeft: '6px'
                        }}>
                          "{card.quote}"
                        </p>
                      </div>

                      {matchingSymbol}

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

          {/* Bottom Lower panel */}
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

          {/* Control Deck */}
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

          {/* Payout Tray */}
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

          {/* Right Physical Lever */}
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
      )}

      {/* Render 3D Gold Luxury Slot Machine */}
      {activeTheme === 'gold' && (
        <div 
          className="slot-cabinet gold-theme-cabinet" 
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            position: 'relative',
            marginRight: '60px',
            overflow: 'visible',
            width: '460px',
            maxHeight: 'calc(100vh - 80px)',
            overflowY: 'visible',
            background: 'linear-gradient(135deg, #8a6f27 0%, #e2c974 25%, #cfa73f 50%, #f7e59b 75%, #8a6f27 100%)',
            border: '6px solid #4a3b10',
            borderRadius: '30px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.85), inset 0 2px 10px rgba(255,255,255,0.4), 0 0 30px rgba(212, 175, 55, 0.25)',
            padding: '16px 16px 24px 16px'
          }}
        >
          {/* 3 top sirens on a curved gold back panel */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-end',
            gap: '24px',
            position: 'absolute',
            top: '-45px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: -1,
            width: '280px',
            height: '60px'
          }}>
            {/* Left siren */}
            <div className={`gold-siren side-siren ${isSpinning ? 'flashing' : ''}`} style={{
              width: '40px',
              height: '40px',
              borderRadius: '50% 50% 0 0',
              background: 'radial-gradient(circle at center, #ff4d4d 30%, #b30000 80%)',
              border: '2px solid #ffd700',
              borderBottom: '4px solid #4a3b10',
              boxShadow: isSpinning ? '0 0 15px #ff4d4d, 0 0 30px #ff4d4d' : '0 4px 6px rgba(0,0,0,0.4)'
            }} />
            {/* Middle larger siren */}
            <div className={`gold-siren center-siren ${isSpinning ? 'flashing' : ''}`} style={{
              width: '54px',
              height: '54px',
              borderRadius: '50% 50% 0 0',
              background: 'radial-gradient(circle at center, #ff3333 30%, #990000 80%)',
              border: '3px solid #ffd700',
              borderBottom: '5px solid #4a3b10',
              boxShadow: isSpinning ? '0 0 25px #ff3333, 0 0 50px #ff3333' : '0 6px 10px rgba(0,0,0,0.4)'
            }} />
            {/* Right siren */}
            <div className={`gold-siren side-siren ${isSpinning ? 'flashing' : ''}`} style={{
              width: '40px',
              height: '40px',
              borderRadius: '50% 50% 0 0',
              background: 'radial-gradient(circle at center, #ff4d4d 30%, #b30000 80%)',
              border: '2px solid #ffd700',
              borderBottom: '4px solid #4a3b10',
              boxShadow: isSpinning ? '0 0 15px #ff4d4d, 0 0 30px #ff4d4d' : '0 4px 6px rgba(0,0,0,0.4)'
            }} />
          </div>

          {/* Arched Top Header like a vintage casino machine */}
          <div style={{
            background: 'radial-gradient(ellipse at center, #261f0a 0%, #0d0a03 100%)',
            border: '3px solid #d4af37',
            borderRadius: '16px',
            padding: '12px 10px',
            textAlign: 'center',
            boxShadow: 'inset 0 0 15px rgba(212,175,55,0.3), 0 4px 10px rgba(0,0,0,0.5)',
            position: 'relative'
          }}>
            <h3 style={{ margin: 0, fontFamily: 'Impact, sans-serif', fontSize: '26px', color: '#ffea7a', letterSpacing: '2px', textShadow: '0 2px 4px #000, 0 0 10px rgba(255,234,122,0.4)' }}>GOLDEN REVERIE</h3>
            <h4 style={{ margin: '2px 0 0 0', fontFamily: 'Arial, sans-serif', fontSize: '10px', fontWeight: 'bold', color: '#ffffff', letterSpacing: '3px', textTransform: 'uppercase', opacity: 0.8 }}>Cognitive Sandbox</h4>
          </div>

          {/* Reel Window Panel */}
          <div style={{
            position: 'relative',
            padding: '20px 18px',
            background: 'linear-gradient(180deg, #1f1a0b 0%, #0d0a03 100%)',
            borderRadius: '20px',
            border: '4px solid #b38728',
            boxShadow: 'inset 0 0 30px rgba(0,0,0,0.95), 0 5px 15px rgba(0,0,0,0.6)',
            overflow: 'visible'
          }}>
            {/* Top lights array in frame */}
            <div style={{ position: 'absolute', top: '7px', left: '16px', right: '16px', display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
              {[...Array(9)].map((_, i) => (
                <div key={i} className={`gold-frame-bulb ${i % 2 === 0 ? 'active' : ''}`} style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: isSpinning ? '#ff3333' : '#ffd700',
                  boxShadow: isSpinning ? '0 0 8px #ff3333' : '0 0 6px #ffd700',
                  transition: 'all 0.1s'
                }} />
              ))}
            </div>

            {/* 3 reels container with gold bezels around each reel */}
            <div className="reel-container" style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
              gap: '14px',
              padding: '10px',
              minHeight: '240px',
              position: 'relative'
            }}>
              {/* Payline */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: 0,
                right: 0,
                height: '3px',
                background: 'linear-gradient(90deg, transparent 5%, #ff3333 30%, #ff3333 70%, transparent 95%)',
                boxShadow: '0 0 8px rgba(255, 51, 51, 0.8)',
                zIndex: 8,
                pointerEvents: 'none'
              }} />

              {[0, 1, 2].map((idx) => {
                const isResolved = spinReelsResolved[idx];
                const card = dueCards[idx];
                const isReviewed = card && reviewedCardIds.has(card.id);
                const isForgotten = card && forgottenCardIds.has(card.id);

                return (
                  <div key={idx} style={{
                    position: 'relative',
                    background: 'linear-gradient(135deg, #aa771c, #fbf5b7, #b38728, #fcf6ba, #aa771c)',
                    padding: '3px',
                    borderRadius: '14px',
                    boxShadow: '0 4px 8px rgba(0,0,0,0.5)',
                    minWidth: 0
                  }}>
                    {/* Inside card wrapper */}
                    <div style={{
                      background: '#0d0a03',
                      borderRadius: '11px',
                      height: '100%',
                      overflow: 'hidden',
                      position: 'relative'
                    }}>
                      {/* If spinning */}
                      {isSpinning && !isResolved ? (
                        <div style={{
                          height: '240px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: '#ffffff',
                          overflow: 'hidden'
                        }}>
                          <div className="reel-spinning-strip" style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '28px',
                            alignItems: 'center',
                            filter: 'blur(2.5px)'
                          }}>
                            {GoldReelSymbols.seven()}
                            {GoldReelSymbols.bell()}
                            {GoldReelSymbols.cherry()}
                            {GoldReelSymbols.bar()}
                            {GoldReelSymbols.seven()}
                            {GoldReelSymbols.bell()}
                            {GoldReelSymbols.cherry()}
                            {GoldReelSymbols.bar()}
                          </div>
                        </div>
                      ) : isResolved && card ? (
                        /* Resolved State with card on white background */
                        <div className={`reel-stop-bounce ${isForgotten ? 'flame-effect' : ''}`} style={{
                          height: '240px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          padding: '14px',
                          background: '#ffffff',
                          color: '#111111',
                          opacity: isReviewed && !isForgotten ? 0.65 : 1,
                          transform: isReviewed && !isForgotten ? 'scale(0.97)' : 'scale(1)',
                          transition: 'opacity 0.4s, transform 0.4s',
                          position: 'relative',
                          boxShadow: 'inset 0 10px 15px rgba(0,0,0,0.1), inset 0 -10px 15px rgba(0,0,0,0.1)'
                        }}>
                          {/* Content */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflow: 'hidden' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              {card.podcast_image_url ? (
                                <img src={card.podcast_image_url} alt="cover" style={{ width: '18px', height: '18px', borderRadius: '4px', objectFit: 'cover', border: '1px solid #ccc' }} />
                              ) : (
                                <div style={{ width: '18px', height: '18px', borderRadius: '4px', background: '#ccc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', fontWeight: 'bold' }}>🎙️</div>
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
                              borderLeft: '2.5px solid #d4af37',
                              paddingLeft: '6px'
                            }}>
                              "{card.quote}"
                            </p>
                          </div>

                          {/* Watermark symbol instead of Emoji badge */}
                          {idx === 0 
                            ? GoldReelSymbols.seven({ position: 'absolute', top: '8px', right: '8px', transform: 'scale(0.55)', transformOrigin: 'top right', opacity: 0.85 })
                            : idx === 1 
                              ? GoldReelSymbols.bell({ position: 'absolute', top: '6px', right: '6px', transform: 'scale(0.55)', transformOrigin: 'top right', opacity: 0.85 })
                              : GoldReelSymbols.cherry({ position: 'absolute', top: '6px', right: '6px', transform: 'scale(0.55)', transformOrigin: 'top right', opacity: 0.85 })
                          }

                          {/* Slider / Action */}
                          <div>
                            {!isReviewed ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#555555', fontWeight: '800' }}>
                                  <span>我已驯服</span>
                                  <span>忘记了</span>
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
                                background: isForgotten ? 'rgba(220, 38, 38, 0.1)' : 'rgba(5, 150, 105, 0.1)',
                                color: isForgotten ? '#dc2626' : '#059669',
                                fontSize: '10px',
                                fontWeight: '900',
                                marginTop: '8px',
                                border: isForgotten ? '1px solid rgba(220, 38, 38, 0.3)' : '1px solid rgba(5, 150, 105, 0.3)',
                              }}>
                                {isForgotten ? '稍后复习' : '已驯服'}
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        /* Idle Default state showing gold seven watermark and text */
                        <div style={{
                          height: '240px',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: '#ffffff',
                          position: 'relative'
                        }}>
                          {idx === 0 ? GoldReelSymbols.seven({ opacity: 0.2, transform: 'scale(1.2)' }) : idx === 1 ? GoldReelSymbols.bell({ opacity: 0.2, transform: 'scale(1.2)' }) : GoldReelSymbols.cherry({ opacity: 0.2, transform: 'scale(1.2)' })}
                          <span style={{ fontSize: '10px', marginTop: '14px', fontWeight: '900', color: '#999', textTransform: 'uppercase', letterSpacing: '1px' }}>REEL {idx + 1} READY</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom lights array in frame */}
            <div style={{ position: 'absolute', bottom: '7px', left: '16px', right: '16px', display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
              {[...Array(9)].map((_, i) => (
                <div key={i} className={`gold-frame-bulb ${i % 2 === 1 ? 'active' : ''}`} style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: isSpinning ? '#ff3333' : '#ffd700',
                  boxShadow: isSpinning ? '0 0 8px #ff3333' : '0 0 6px #ffd700',
                  transition: 'all 0.1s'
                }} />
              ))}
            </div>
          </div>

          {/* 3D Golden Control Platform with 3 Red Push Buttons */}
          <div style={{
            background: 'linear-gradient(180deg, #aa771c 0%, #ffd700 30%, #e2c974 70%, #8a6f27 100%)',
            border: '3px solid #4a3b10',
            borderRadius: '12px',
            padding: '12px 20px',
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            boxShadow: '0 6px 12px rgba(0,0,0,0.5), inset 0 2px 4px rgba(255,255,255,0.6)',
            position: 'relative'
          }}>
            {/* Button 1: SPIN */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={triggerLeverPull}
                disabled={isSpinning}
                className="gold-deck-btn"
                style={{
                  width: '45px',
                  height: '45px',
                  borderRadius: '50%',
                  border: '3px solid #5a0000',
                  background: 'radial-gradient(circle at 12px 12px, #ff4d4d, #b30000 65%, #660000 100%)',
                  boxShadow: isSpinning ? 'none' : '0 4px 6px rgba(0,0,0,0.4), inset 0 2px 4px rgba(255,255,255,0.5)',
                  cursor: isSpinning ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'transform 0.1s, box-shadow 0.1s',
                  transform: isSpinning ? 'translateY(2px)' : 'none'
                }}
                onMouseDown={(e) => { if(!isSpinning) e.currentTarget.style.transform = 'translateY(2px)'; }}
                onMouseUp={(e) => { if(!isSpinning) e.currentTarget.style.transform = 'none'; }}
              >
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'rgba(255,255,255,0.25)', position: 'absolute', top: '6px', left: '10px' }} />
              </button>
              <span style={{ fontSize: '9px', fontWeight: '900', color: '#332400', textTransform: 'uppercase', fontFamily: 'Arial, sans-serif' }}>SPIN</span>
            </div>

            {/* Button 2: AUTO */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={handleSpinSlotMachine}
                disabled={isSpinning}
                className="gold-deck-btn"
                style={{
                  width: '45px',
                  height: '45px',
                  borderRadius: '50%',
                  border: '3px solid #5a0000',
                  background: 'radial-gradient(circle at 12px 12px, #ff4d4d, #b30000 65%, #660000 100%)',
                  boxShadow: isSpinning ? 'none' : '0 4px 6px rgba(0,0,0,0.4), inset 0 2px 4px rgba(255,255,255,0.5)',
                  cursor: isSpinning ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'transform 0.1s, box-shadow 0.1s',
                  transform: isSpinning ? 'translateY(2px)' : 'none'
                }}
                onMouseDown={(e) => { if(!isSpinning) e.currentTarget.style.transform = 'translateY(2px)'; }}
                onMouseUp={(e) => { if(!isSpinning) e.currentTarget.style.transform = 'none'; }}
              >
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'rgba(255,255,255,0.25)', position: 'absolute', top: '6px', left: '10px' }} />
              </button>
              <span style={{ fontSize: '9px', fontWeight: '900', color: '#332400', textTransform: 'uppercase', fontFamily: 'Arial, sans-serif' }}>AUTO</span>
            </div>

            {/* Button 3: PLAY */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={triggerLeverPull}
                disabled={isSpinning}
                className="gold-deck-btn"
                style={{
                  width: '45px',
                  height: '45px',
                  borderRadius: '50%',
                  border: '3px solid #5a0000',
                  background: 'radial-gradient(circle at 12px 12px, #ff4d4d, #b30000 65%, #660000 100%)',
                  boxShadow: isSpinning ? 'none' : '0 4px 6px rgba(0,0,0,0.4), inset 0 2px 4px rgba(255,255,255,0.5)',
                  cursor: isSpinning ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'transform 0.1s, box-shadow 0.1s',
                  transform: isSpinning ? 'translateY(2px)' : 'none'
                }}
                onMouseDown={(e) => { if(!isSpinning) e.currentTarget.style.transform = 'translateY(2px)'; }}
                onMouseUp={(e) => { if(!isSpinning) e.currentTarget.style.transform = 'none'; }}
              >
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'rgba(255,255,255,0.25)', position: 'absolute', top: '6px', left: '10px' }} />
              </button>
              <span style={{ fontSize: '9px', fontWeight: '900', color: '#332400', textTransform: 'uppercase', fontFamily: 'Arial, sans-serif' }}>PLAY</span>
            </div>
          </div>

          {/* Curved Base with glass display of SPIN text logo & gold coins */}
          <div style={{
            background: 'linear-gradient(180deg, #8a6f27 0%, #3a2e0a 100%)',
            border: '3px solid #4a3b10',
            borderRadius: '16px',
            padding: '12px',
            boxShadow: '0 6px 12px rgba(0,0,0,0.5), inset 0 2px 4px rgba(255,255,255,0.4)',
            position: 'relative',
            height: '110px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            alignItems: 'center'
          }}>
            <div style={{
              position: 'absolute',
              top: '8px',
              left: '8px',
              right: '8px',
              bottom: '8px',
              borderRadius: '10px',
              border: '2px solid #b38728',
              background: 'linear-gradient(180deg, rgba(26,20,5,0.95) 0%, rgba(13,10,2,0.95) 100%)',
              boxShadow: 'inset 0 0 15px rgba(0,0,0,0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              zIndex: 1
            }}>
              <div style={{
                position: 'absolute',
                bottom: '-25px',
                left: 0,
                right: 0,
                display: 'flex',
                justifyContent: 'center',
                flexWrap: 'wrap',
                gap: '2px',
                opacity: 0.75,
                zIndex: 1
              }}>
                {[...Array(24)].map((_, i) => (
                  <div key={i} className="gold-coin" style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #ffd700 0%, #b38728 50%, #fcf6ba 100%)',
                    border: '1px solid #aa771c',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    transform: `translateY(${Math.sin(i) * 5}px) rotate(${i * 15}deg)`,
                    margin: '-4px'
                  }} />
                ))}
              </div>

              <div style={{
                fontFamily: "'Impact', 'Arial Black', sans-serif",
                fontSize: '36px',
                fontWeight: '900',
                color: '#ef4444',
                letterSpacing: '6px',
                textAlign: 'center',
                textTransform: 'uppercase',
                textShadow: '0 0 15px rgba(239, 68, 68, 0.8), 0 3px 6px #000',
                zIndex: 2,
                animation: isSpinning ? 'pulse-neon 0.6s infinite alternate' : 'none',
                userSelect: 'none'
              }}>
                SPIN
              </div>

              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                background: 'linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 40%, transparent 60%, rgba(0,0,0,0.2) 100%)',
                pointerEvents: 'none',
                zIndex: 3
              }} />
            </div>
          </div>

          {/* Right side Golden Lever */}
          <div 
            onClick={triggerLeverPull}
            style={{
              width: '60px',
              height: '220px',
              position: 'absolute',
              right: '-52px',
              top: '140px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end',
              cursor: isSpinning ? 'not-allowed' : 'pointer',
              userSelect: 'none',
              zIndex: 10
            }}
          >
            <div style={{
              width: '24px',
              height: '40px',
              background: 'linear-gradient(90deg, #aa771c 0%, #ffd700 50%, #8a6f27 100%)',
              border: '2px solid #5e470f',
              borderRadius: '4px',
              position: 'absolute',
              bottom: '20px',
              left: '18px',
              boxShadow: '0 4px 8px rgba(0,0,0,0.6)'
            }} />
            
            <div style={{
              width: '8px',
              height: '110px',
              background: 'linear-gradient(90deg, #bf953f 0%, #fcf6ba 50%, #b38728 100%)',
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
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'radial-gradient(circle at 10px 10px, #ff4d4d, #990000 60%, #4a0000 100%)',
                position: 'absolute',
                top: '-26px',
                left: '-12px',
                boxShadow: isSpinning ? '0 0 16px #ff4d4d' : '0 6px 12px rgba(0,0,0,0.4)',
                border: '1.5px solid rgba(255,255,255,0.3)'
              }} />
            </div>
          </div>

          {/* 3D Reflection below cabinet */}
          <div style={{
            position: 'absolute',
            bottom: '-120px',
            left: '20px',
            right: '20px',
            height: '100px',
            background: 'linear-gradient(180deg, rgba(212,175,55,0.25) 0%, rgba(212,175,55,0.05) 50%, transparent 100%)',
            borderRadius: '30px',
            filter: 'blur(8px)',
            transform: 'scaleY(-0.3)',
            pointerEvents: 'none',
            zIndex: -5
          }} />
        </div>
      )}
    </div>
  );
}
