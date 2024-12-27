import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, Tooltip, Line, CartesianGrid } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const WifiMonitor = () => {
  const [packetData, setPacketData] = useState([]);
  const [statistics, setStatistics] = useState({
    totalPackets: 0,
    uniqueDevices: new Set(),
    signalStrengths: []
  });

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:5000/ws');
    
    ws.onmessage = (event) => {
      const packet = JSON.parse(event.data);
      setPacketData(prev => [...prev, packet].slice(-100));
      
      setStatistics(prev => ({
        totalPackets: prev.totalPackets + 1,
        uniqueDevices: new Set([...prev.uniqueDevices, packet.src]),
        signalStrengths: [...prev.signalStrengths, packet.signal_strength].slice(-100)
      }));
    };

    return () => ws.close();
  }, []);

  return (
    <div className="p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>WiFi Monitor Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="p-4 bg-blue-100 rounded">
              <h3 className="text-lg font-semibold">Total Packets</h3>
              <p className="text-2xl">{statistics.totalPackets}</p>
            </div>
            <div className="p-4 bg-green-100 rounded">
              <h3 className="text-lg font-semibold">Unique Devices</h3>
              <p className="text-2xl">{statistics.uniqueDevices.size}</p>
            </div>
            <div className="p-4 bg-purple-100 rounded">
              <h3 className="text-lg font-semibold">Avg Signal Strength</h3>
              <p className="text-2xl">
                {statistics.signalStrengths.length > 0
                  ? Math.round(
                      statistics.signalStrengths.reduce((a, b) => a + b) /
                        statistics.signalStrengths.length
                    )
                  : 0}
                 dBm
              </p>
            </div>
          </div>
          
          <div className="h-64">
            <LineChart width={800} height={200} data={packetData}>
              <XAxis dataKey="timestamp" />
              <YAxis />
              <CartesianGrid strokeDasharray="3 3" />
              <Tooltip />
              <Line type="monotone" dataKey="signal_strength" stroke="#8884d8" />
            </LineChart>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WifiMonitor;
