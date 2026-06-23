import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';
import RobotRow from '@/components/molecules/RobotRow';
import SearchInput from '@/components/molecules/SearchInput';
import StatusIndicator from '@/components/atoms/StatusIndicator';

export default function Sidebar() {
  const { t } = useTranslation();
  const { robots, selectedRobotId, selectRobot } = useRobotContext();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filtered = robots.filter((r) => {
    const matchesSearch = r.robotId.toLowerCase().includes(search.toLowerCase())
      || r.name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const onlineCount = robots.filter((r) => r.status === 'online').length;
  const errorCount = robots.filter((r) => r.status === 'error').length;
  const warningCount = robots.filter((r) => r.status === 'warning').length;

  return (
    <aside
      className="w-64 flex-shrink-0 border-r flex flex-col h-full"
      style={{
        backgroundColor: 'var(--bg-sidebar)',
        borderColor: 'var(--border-light)',
      }}
      role="navigation"
      aria-label="机器人列表"
    >
      {/* Search */}
      <div className="p-3">
        <SearchInput value={search} onChange={setSearch} placeholder={t('common.search')} />
      </div>

      {/* Status filter chips */}
      <div className="flex gap-1 px-3 pb-2">
        {[
          { key: 'all', label: t('common.all'), count: robots.length },
          { key: 'online', label: t('status.online'), count: onlineCount },
          { key: 'warning', label: t('status.warning'), count: warningCount },
          { key: 'error', label: t('status.error'), count: errorCount },
        ].map((chip) => (
          <button
            key={chip.key}
            onClick={() => setStatusFilter(chip.key)}
            className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium transition-colors"
            style={{
              backgroundColor: statusFilter === chip.key ? '#2563EB' : 'var(--bg-hover)',
              color: statusFilter === chip.key ? '#FFFFFF' : 'var(--text-secondary)',
            }}
          >
            {chip.label}
            <span className="opacity-80">{chip.count}</span>
          </button>
        ))}
      </div>

      {/* Robot list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-sm" style={{ color: 'var(--text-tertiary)' }}>
            {t('common.noData')}
          </div>
        ) : (
          filtered.map((robot) => (
            <RobotRow
              key={robot.robotId}
              robot={robot}
              selected={robot.robotId === selectedRobotId}
              onClick={() => selectRobot(robot.robotId)}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div
        className="px-3 py-2 border-t text-[10px] flex items-center justify-between"
        style={{ borderColor: 'var(--border-light)', color: 'var(--text-tertiary)' }}
      >
        <span>{filtered.length}/{robots.length} {t('common.robots')}</span>
        <button
          onClick={() => setSearch('')}
          className="hover:text-[var(--text-link)] transition-colors"
        >
          {t('common.refresh')}
        </button>
      </div>
    </aside>
  );
}
