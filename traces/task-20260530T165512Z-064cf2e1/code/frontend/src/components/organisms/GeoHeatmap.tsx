import { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { ScatterChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent, VisualMapComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import ChartCard from '@/components/molecules/ChartCard';
import { useTheme } from '@/contexts/ThemeContext';
import { useTranslation } from 'react-i18next';
import type { SimulatedRobot } from '@/types';

echarts.use([ScatterChart, GridComponent, TooltipComponent, TitleComponent, VisualMapComponent, CanvasRenderer]);

interface GeoHeatmapProps {
  robots: SimulatedRobot[];
}

export default function GeoHeatmap({ robots }: GeoHeatmapProps) {
  const { theme } = useTheme();
  const { t } = useTranslation();

  const option = useMemo(() => {
    const textColor = theme === 'dark' ? '#9CA3AF' : '#6B7280';

    const data = robots.map((r) => ({
      value: [r.location.longitude, r.location.latitude],
      name: r.robotId,
      symbolSize: Math.max(8, Math.min(30, r.battery.levelPercent * 0.3)),
      itemStyle: {
        color:
          r.status === 'error' ? '#EF4444'
          : r.status === 'warning' ? '#F59E0B'
          : r.battery.levelPercent < 20 ? '#F59E0B'
          : '#10B981',
      },
    }));

    return {
      grid: {
        top: 8,
        right: 16,
        bottom: 16,
        left: 48,
      },
      xAxis: {
        type: 'value' as const,
        name: '经度',
        nameLocation: 'middle' as const,
        nameGap: 24,
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: textColor } },
        axisLabel: { color: textColor, fontSize: 10, formatter: (v: number) => v.toFixed(4) },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value' as const,
        name: '纬度',
        nameTextStyle: { color: textColor, fontSize: 10 },
        axisLine: { lineStyle: { color: textColor } },
        axisLabel: { color: textColor, fontSize: 10, formatter: (v: number) => v.toFixed(4) },
        splitLine: { show: false },
      },
      tooltip: {
        trigger: 'item' as const,
        formatter: (params: { name: string; value: number[] }) => {
          const robot = robots.find((r) => r.robotId === params.name);
          if (!robot) return params.name;
          return `<b>${robot.robotId}</b> (${robot.name})<br/>
            电量: ${robot.battery.levelPercent}%<br/>
            状态: ${robot.status}<br/>
            位置: [${params.value[1].toFixed(4)}, ${params.value[0].toFixed(4)}]`;
        },
      },
      series: [
        {
          type: 'scatter',
          data,
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' },
          },
        },
      ],
    };
  }, [robots, theme]);

  return (
    <ChartCard title={t('charts.geoHeatmap')}>
      <ReactEChartsCore echarts={echarts} option={option} style={{ height: '100%', width: '100%' }} notMerge />
      <table className="sr-only" aria-label="机器人位置数据">
        <caption>{t('charts.geoHeatmap')}</caption>
        <thead><tr><th>机器人</th><th>经度</th><th>纬度</th><th>状态</th></tr></thead>
        <tbody>
          {robots.map((r) => (
            <tr key={r.robotId}>
              <td>{r.robotId}</td>
              <td>{r.location.longitude.toFixed(4)}</td>
              <td>{r.location.latitude.toFixed(4)}</td>
              <td>{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </ChartCard>
  );
}
