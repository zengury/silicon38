import { useTranslation } from 'react-i18next';
import { useTheme } from '@/contexts/ThemeContext';
import ExportDropdown from '@/components/molecules/ExportDropdown';
import IconButton from '@/components/atoms/IconButton';
import Button from '@/components/atoms/Button';

interface HeaderProps {
  onToggleFleetOverview: () => void;
  onToggleTimeline: () => void;
  fleetOverviewExpanded: boolean;
  timelineOpen: boolean;
}

export default function Header({ onToggleFleetOverview, onToggleTimeline, fleetOverviewExpanded, timelineOpen }: HeaderProps) {
  const { t, i18n } = useTranslation();
  const { theme, toggleTheme } = useTheme();

  function handleExport(format: 'pdf' | 'excel') {
    alert(`${format === 'pdf' ? 'PDF' : 'Excel'} ${t('export.generating')}`);
  }

  return (
    <header
      className="flex items-center justify-between px-6 h-14 border-b flex-shrink-0"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-light)',
        zIndex: 'var(--z-sticky)',
      }}
    >
      {/* Left: Logo + Title */}
      <div className="flex items-center gap-3">
        <svg width={28} height={28} viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <rect width="32" height="32" rx="8" fill="#2563EB" />
          <path d="M16 6l-8 12h5l-2 8 10-14h-4l3-6z" fill="white" />
        </svg>
        <h1 className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>
          {t('app.shortTitle')}
        </h1>
      </div>

      {/* Center: View toggles */}
      <div className="flex items-center gap-1">
        <Button
          variant={fleetOverviewExpanded ? 'primary' : 'ghost'}
          size="sm"
          onClick={onToggleFleetOverview}
        >
          {t('charts.fleetOverview')}
        </Button>
        <Button
          variant={timelineOpen ? 'primary' : 'ghost'}
          size="sm"
          onClick={onToggleTimeline}
        >
          {t('common.timeline')}
        </Button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <ExportDropdown onExport={handleExport} />

        {/* Theme toggle */}
        <IconButton
          label={t('theme.switch')}
          onClick={toggleTheme}
        >
          {theme === 'dark' ? (
            <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </IconButton>

        {/* Language toggle */}
        <IconButton
          label={t('lang.switch')}
          onClick={() => i18n.changeLanguage(i18n.language === 'zh-CN' ? 'en' : 'zh-CN')}
        >
          <span className="text-xs font-bold">{i18n.language === 'zh-CN' ? 'EN' : '中'}</span>
        </IconButton>
      </div>
    </header>
  );
}
