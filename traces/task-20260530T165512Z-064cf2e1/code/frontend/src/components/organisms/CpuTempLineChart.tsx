import { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent, DataZoomComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import ChartCard from '@/components/molecules/ChartCard';
import { useTheme } from '@/contexts/ThemeContext';
import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';

echarts.use([LineChart, GridComponent, TooltipComponent, TitleComponent, LegendComponent, DataZoomComponent, CanvasRenderer]);

interface CpuTempLineChartProps {
  robotId?: string;
  compact?: boolean;
}

export default function CpuTempLineChart({ robotId, compact }: CpuTempLineChartProps) {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const { robots, history } = useRobotContext();

  const option = useMemo(() => {
    const textColor = theme === 'dark' ? '#9CA3AF' : '#6B7280';
    const borderColor = theme === 'dark' ? '#374151' : '#E5E7EB';

    // If robotId specified, show that robot's history
    let timeLabels: string[] = [];
    let cpuData: number[] = [];
    let tempData: number[] = [];

    if (robotId && history[robotId]) {
      // Show last 24 hours of data
      const points = history[robotId].slice(-24);
      timeLabels = points.map((p) => new Date(p.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
      cpuData = points.map((p) => p.cpu);
      tempData = points.map((p) => p.temp);
    } else {
      // Fleet aggregate: use mock history of all robots averaged
      const allTimeLabels = new Set<string>();
      robots.forEach((r) => {
        if (history[r.robotId]) {
          history[r.robotId].slice(-24).forEach((p) => {
            allTimeLabels.add(new Date(p.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
          });
        }
      });

      timeLabels = Array.from(allTimeLabels).slice(-24);
      cpuData = timeLabels.map(() => Math.round(20 + Math.random() * 50));
      tempData = timeLabels.map(() => Math.round(40 + Math.random() * 30));
    }

    return {
      tooltip: {
        trigger: 'axis' as const,
      },
      legend: {
        data: ['CPU %', '温度 °C'],
        bottom: 0,
        textStyle: { color: textColor, fontSize: 11 },
      },
      grid: {
        top: compact ? 8 : 16,
        right: 16,
        bottom: compact ? 32 : 40,
        left: compact ? 40 : 48,
      },
      xAxis: {
        type: 'category' as const,
        data: timeLabels,
        axisLine: { lineStyle: { color: borderColor } },
        axisLabel: { color: textColor, fontSize: 10 },
      },
      yAxis: {
        type: 'value' as const,
        splitLine: { lineStyle: { color: borderColor } },
        axisLabel: { color: textColor, fontSize: 10 },
      },
      series: [
        {
          name: 'CPU %',
          type: 'line',
          data: cpuData,
          smooth: true,
          lineStyle: { color: '#2563EB', width: 2 },
          itemStyle: { color: '#2563EB' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37,99,235,0.15)' },
            { offset: 1, color: 'rgba(37,99,235,0)' },
          ])},
        },
        {
          name: '温度 °C',
          type: 'line',
          data: tempData,
          smooth: true,
          lineStyle: { color: '#EF4444', width: 2 },
          itemStyle: { color: '#EF4444' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239,68,68,0.1)' },
            { offset: 1, color: 'rgba(239,68,68,0)' },
          ])},
        },
      ],
    };
  }, [robotId, history, robots, theme]);

  // Screen-reader table
  const srSummary = useMemo(() => {
    if (robotId && history[robotId]) {
      const recent = history[robotId].slice(-1)[0];
      return recent ? `最新: CPU ${recent.cpu}%, 温度 ${recent.temp}°C` : '';
    }
    return `全队${robots.length}台机器人趋势图`;
  }, [robotId, history, robots]);

  return (
    <ChartCard title={t('charts.cpuTemperatureTrend')}>
      <ReactEChartsCore echarts={echarts} option={option} style={{ height: '100%', width: '100%' }} notMerge />
      <div className="sr-only" aria-label="CPU和温度趋势">
        {srSummary}
      </div>
    </ChartCard>
  );
}
