import { useState, useCallback, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

/**
 * 全局 Dialog 组件 — 替代原生 alert() / confirm()
 *
 * 用法：通过 useDialog() hook 获取 dialog / alert / confirm 方法
 */

let _setDialogState = null;

function DialogRenderer() {
  const [state, setState] = useState(null);
  _setDialogState = setState;

  const handleConfirm = useCallback(() => {
    if (state?.onConfirm) state.onConfirm();
    setState(null);
  }, [state]);

  const handleCancel = useCallback(() => {
    if (state?.onCancel) state.onCancel();
    setState(null);
  }, [state]);

  // ESC 关闭
  useEffect(() => {
    if (!state) return;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleCancel();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [state, handleCancel]);

  if (!state) return null;

  const isConfirm = state.mode === 'confirm';
  const iconMap = {
    warning: <AlertTriangle size={22} className="text-[var(--accent-red)]" />,
    success: <CheckCircle size={22} className="text-emerald-500" />,
    info: <Info size={22} className="text-[var(--accent-blue)]" />,
  };
  const icon = iconMap[state.variant] || iconMap.warning;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[200] p-6 animate-fade-in">
      <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/50 rounded-xl max-w-sm w-full relative flex flex-col shadow-2xl transition-colors duration-300">
        {/* Header */}
        <div className="p-5 pb-0 flex items-start gap-3">
          <div className="mt-0.5 shrink-0">{icon}</div>
          <div className="flex-1 min-w-0">
            {state.title && (
              <h3 className="text-base font-bold text-[var(--text-primary)] mb-1">
                {state.title}
              </h3>
            )}
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {state.message}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="p-5 pt-4 flex justify-end gap-2">
          {isConfirm && (
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-sm font-semibold rounded-lg border border-[var(--border-primary)]/40 text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors cursor-pointer bg-transparent"
            >
              {state.cancelText || '取消'}
            </button>
          )}
          <button
            onClick={handleConfirm}
            autoFocus
            className={`px-4 py-2 text-sm font-bold rounded-lg transition-all cursor-pointer border-0 outline-none ${
              state.variant === 'success'
                ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                : 'bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white'
            }`}
          >
            {state.confirmText || (isConfirm ? '确定' : '好的')}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * alert(message, options?) — 替代 window.alert
 * @param {string} message
 * @param {object} [options] - { title?, variant?, confirmText? }
 * @returns {Promise<void>}
 */
export function alert(message, options = {}) {
  return new Promise((resolve) => {
    _setDialogState({
      mode: 'alert',
      message,
      title: options.title,
      variant: options.variant || 'warning',
      confirmText: options.confirmText,
      onConfirm: () => resolve(),
      onCancel: () => resolve(),
    });
  });
}

/**
 * confirm(message, options?) — 替代 window.confirm
 * @param {string} message
 * @param {object} [options] - { title?, variant?, confirmText?, cancelText? }
 * @returns {Promise<boolean>}
 */
export function confirm(message, options = {}) {
  return new Promise((resolve) => {
    _setDialogState({
      mode: 'confirm',
      message,
      title: options.title,
      variant: options.variant || 'warning',
      confirmText: options.confirmText,
      cancelText: options.cancelText,
      onConfirm: () => resolve(true),
      onCancel: () => resolve(false),
    });
  });
}

export default DialogRenderer;
