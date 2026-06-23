import { useRobotContext } from '@/contexts/RobotContext';
import Header from '@/components/organisms/Header';
import Sidebar from '@/components/organisms/Sidebar';
import DashboardGrid from '@/components/organisms/DashboardGrid';
import RobotDetailSheet from '@/components/organisms/RobotDetailSheet';
import TimelineDrawer from '@/components/organisms/TimelineDrawer';
import AlertBanner from '@/components/molecules/AlertBanner';

export default function DashboardLayout() {
  const {
    selectedRobotId,
    fleetOverviewExpanded,
    timelineOpen,
    alerts,
    selectRobot,
    toggleFleetOverview,
    toggleTimeline,
    dispatch,
  } = useRobotContext();

  // Show active critical alerts as banner
  const activeCritical = alerts.filter((a) => !a.acknowledgedAt && a.severity === 'critical');
  const activeWarning = alerts.filter((a) => !a.acknowledgedAt && a.severity === 'warning');

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: 'var(--bg-root)' }}>
      {/* Header */}
      <Header
        onToggleFleetOverview={toggleFleetOverview}
        onToggleTimeline={toggleTimeline}
        fleetOverviewExpanded={fleetOverviewExpanded}
        timelineOpen={timelineOpen}
      />

      {/* Alert banners */}
      {activeCritical.length > 0 && (
        <AlertBanner
          message={`${activeCritical.length} 条严重告警待处理`}
          severity="critical"
          onAcknowledge={() => activeCritical.forEach((a) =>
            dispatch({ type: 'ACKNOWLEDGE_ALERT', alertId: a.alertId, userId: 'current-user' })
          )}
          onViewDetails={() => selectRobot(activeCritical[0].robotId)}
        />
      )}
      {activeWarning.length > 0 && !activeCritical.length && (
        <AlertBanner
          message={`${activeWarning.length} 条警告`}
          severity="warning"
          onDismiss={() => {}}
        />
      )}

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar (Variant B) */}
        <Sidebar />

        {/* Content - Fleet overview or Robot detail */}
        <main className="flex-1 flex overflow-hidden">
          {fleetOverviewExpanded && !selectedRobotId ? (
            <DashboardGrid />
          ) : selectedRobotId ? (
            <RobotDetailSheet />
          ) : (
            <DashboardGrid />
          )}
        </main>

        {/* Timeline drawer (Variant C) */}
        {timelineOpen && <TimelineDrawer />}
      </div>
    </div>
  );
}
