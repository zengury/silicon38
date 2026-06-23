import { ThemeProvider } from '@/contexts/ThemeContext';
import { RobotProvider } from '@/contexts/RobotContext';
import DashboardLayout from '@/components/templates/DashboardLayout';

export default function App() {
  return (
    <ThemeProvider>
      <RobotProvider>
        <DashboardLayout />
      </RobotProvider>
    </ThemeProvider>
  );
}
