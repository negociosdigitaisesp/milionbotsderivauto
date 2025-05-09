
import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine,
  Legend
} from 'recharts';

interface PerformanceData {
  date: string;
  value: number;
}

interface PerformanceChartProps {
  data: PerformanceData[];
  isPositive: boolean;
  title: string;
  yAxisLabel?: string;
  showAverage?: boolean;
  animationActive?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const value = payload[0].value;
    let accuracyLevel;
    let accuracyColor;
    
    if (value >= 60) {
      accuracyLevel = 'Alta';
      accuracyColor = 'text-success';
    } else if (value >= 45) {
      accuracyLevel = 'Moderada';
      accuracyColor = 'text-warning';
    } else {
      accuracyLevel = 'Baixa';
      accuracyColor = 'text-danger';
    }
    
    return (
      <div className="bg-background border border-border p-2 rounded-md shadow-md">
        <p className="text-sm font-medium">{label}</p>
        <p className={`text-sm ${accuracyColor}`}>
          Precisão: <span className="font-bold">{value}%</span>
        </p>
        <p className="text-xs text-muted-foreground">
          Assertividade {accuracyLevel}
        </p>
      </div>
    );
  }

  return null;
};

const PerformanceChart = ({ 
  data, 
  isPositive, 
  title, 
  yAxisLabel,
  showAverage = true,
  animationActive = true
}: PerformanceChartProps) => {
  // Calculate min and max for better visualization
  const values = data.map(item => item.value);
  const minValue = Math.max(0, Math.floor(Math.min(...values) - 5));
  const maxValue = Math.min(100, Math.ceil(Math.max(...values) + 5));
  
  // Find average value
  const avgValue = values.reduce((sum, val) => sum + val, 0) / values.length;
  
  // Determine chart colors based on average value
  let areaColor, areaGradientId, referenceLineColor;
  
  if (isPositive) {
    areaColor = "#4CAF50";
    areaGradientId = "colorPositive";
    referenceLineColor = "rgba(76,175,80,0.6)";
  } else if (avgValue >= 50) {
    areaColor = "#FFA726";
    areaGradientId = "colorNeutral";
    referenceLineColor = "rgba(255,167,38,0.6)";
  } else {
    areaColor = "#F44336";
    areaGradientId = "colorNegative";
    referenceLineColor = "rgba(244,67,54,0.6)";
  }
  
  return (
    <div className="rounded-lg bg-card">
      {title && <h3 className="text-base font-medium mb-2 px-4 pt-4">{title}</h3>}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{
              top: 10,
              right: 20,
              left: 10,
              bottom: 10,
            }}
          >
            <defs>
              <linearGradient id="colorPositive" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4CAF50" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#4CAF50" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorNegative" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F44336" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#F44336" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorNeutral" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FFA726" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#FFA726" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10, fill: '#999' }}
              tickLine={{ stroke: '#555' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
            />
            <YAxis 
              tick={{ fontSize: 10, fill: '#999' }}
              tickLine={{ stroke: '#555' }}
              domain={[minValue, maxValue]}
              axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              label={{ 
                value: yAxisLabel, 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#999', fontSize: 12 }  
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            {showAverage && (
              <>
                <ReferenceLine 
                  y={50} 
                  stroke="rgba(255,255,255,0.3)" 
                  strokeDasharray="3 3" 
                  label={{ 
                    value: "50%", 
                    position: "right",
                    fill: "rgba(255,255,255,0.5)",
                    fontSize: 10
                  }} 
                />
                <ReferenceLine 
                  y={avgValue} 
                  stroke={referenceLineColor} 
                  strokeDasharray="3 3"
                  label={{ 
                    value: `Média: ${avgValue.toFixed(1)}%`, 
                    position: "left",
                    fill: referenceLineColor.replace(/0\.\d+\)$/, "0.8)"),
                    fontSize: 10
                  }}
                />
              </>
            )}
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke={areaColor} 
              fillOpacity={0.8}
              fill={`url(#${areaGradientId})`} 
              activeDot={{ r: 6, stroke: "#fff", strokeWidth: 2 }}
              animationDuration={animationActive ? 1500 : 0}
              animationEasing="ease-out"
            />
            <Legend 
              verticalAlign="top" 
              height={36}
              formatter={(value) => {
                if (value === 'value') return 'Assertividade (%)';
                return value;
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceChart;
