import { useState, useRef, useEffect } from 'react';
import Button from '@/components/atoms/Button';
import { useTranslation } from 'react-i18next';

interface ExportDropdownProps {
  onExport: (format: 'pdf' | 'excel') => void;
}

export default function ExportDropdown({ onExport }: ExportDropdownProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <Button
        variant="secondary"
        size="sm"
        onClick={() => setOpen(!open)}
        icon={
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        }
      >
        {t('export.title')}
      </Button>
      {open && (
        <div
          className="absolute right-0 mt-2 w-48 rounded-lg shadow-dropdown border py-1 z-[var(--z-dropdown)] animate-fade-in"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-light)' }}
        >
          <button
            onClick={() => { onExport('pdf'); setOpen(false); }}
            className="w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--bg-hover)] flex items-center gap-3"
            style={{ color: 'var(--text-primary)' }}
          >
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            {t('export.pdf')}
          </button>
          <button
            onClick={() => { onExport('excel'); setOpen(false); }}
            className="w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--bg-hover)] flex items-center gap-3"
            style={{ color: 'var(--text-primary)' }}
          >
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <line x1="3" y1="9" x2="21" y2="9" />
              <line x1="3" y1="15" x2="21" y2="15" />
              <line x1="9" y1="3" x2="9" y2="21" />
            </svg>
            {t('export.excel')}
          </button>
        </div>
      )}
    </div>
  );
}
