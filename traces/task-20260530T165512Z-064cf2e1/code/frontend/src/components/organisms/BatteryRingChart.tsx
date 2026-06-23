import { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import ChartCard from '@/components/molecules/ChartCard';
import { useTheme } from '@/contexts/ThemeContext';
import { useTranslation } from 'react-i18next';
import type { SimulatedRobot } from '@/types';

echarts.use([PieChart, GridComponent, TooltipComponent, TitleComponent, LegendComponent, CanvasRenderer]);

interface BatteryRingChartProps {
  robots: SimulatedRobot[];
}

export default function BatteryRingChart({ robots }: BatteryRingChartProps) {
  const { theme } = useTheme();
  const { t } = useTranslation();

  const option = useMemo(() => {
    const ranges = [
      { name: '高 (≥60%)', min: 60, max: 100, color: '#10B981' },
      { name: '中 (20-59%)', min: 20, max: 59.9, color: '#F59E0B' },
      { name: '低 (<20%)', min: 0, max: 19.9, color: '#EF4444' },
    ];

    const data = ranges.map((r) => ({
      name: r.name,
      value: robots.filter((rb) => rb.battery.levelPercent >= r.min && rb.battery.levelPercent <= r.max).length,
      itemStyle: { color: r.color },
    }));

    return {
      tooltip: {
        trigger: 'item' as const,
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        bottom: 0,
        textStyle: {
          color: theme === 'dark' ? '#9CA3AF' : '#6B7280',
          fontSize: 11,
        },
      },
      series: [
        {
          type: 'pie',
          radius: ['55%', '80%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: 16, fontWeight: 'bold' },
          },
          data,
        },
      ],
    };
  }, [robots, theme]);

  // Screen-reader table
  const srData = useMemo(() => {
    const high = robots.filter((r) => r.battery.levelPercent >= 60).length;
    const mid = robots.filter((r) => r.battery.levelPercent >= 20 && r.battery.levelPercent < 60).length;
    const low = robots.filter((r) => r.battery.levelPercent < 20).length;
    return { high, mid, low, total: robots.length };
  }, [robots]);

  return (
    <ChartCard title={t('charts.batteryDistribution')}>
      <ReactEChartsCore echarts={echarts} option={option} style={{ height: '100%', width: '100%' }} notMerge />
      <table className="sr-only" aria-label="电量分布数据">
        <caption>{t('charts.batteryDistribution')}</caption>
        <thead><tr><th>区间</th><th>数量</th></tr></thead>
        <tbody>
          <tr><td>高电量</td><td>{srData.high}</td></tr>
          <tr><td>中电量</td><td>{srData.mid}</td></tr>
          <tr><td>低电量</td><td>{srData.low}</td></tr>
        </tbody>
      </table>
    </ChartCard>
  );
}
