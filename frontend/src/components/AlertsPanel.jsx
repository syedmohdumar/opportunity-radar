import React from 'react';
import { Bell, CheckCheck, AlertTriangle, Info, AlertCircle } from 'lucide-react';

const priorityIcons = {
  critical: AlertTriangle,
  high: AlertCircle,
  medium: Info,
  low: Info,
};

export default function AlertsPanel({ alerts, onMarkRead }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">
          <Bell className="w-8 h-8 text-[#A0A7B4]" />
        </div>
        <p className="text-sm text-[#7F8FA4] mt-3 font-medium">No alerts yet</p>
        <p className="text-xs text-[#A0A7B4]">Run a scan to detect signals and generate alerts</p>
      </div>
    );
  }

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">Alerts</h2>
          <p className="section-subtitle">{alerts.filter(a => !a.is_read).length} unread</p>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        {alerts.map((alert) => {
          const Icon = priorityIcons[alert.priority] || Info;
          return (
            <div
              key={alert.id}
              className={`alert-item ${alert.priority} ${alert.is_read ? 'read' : ''}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${
                    alert.priority === 'critical' ? 'text-red-400' :
                    alert.priority === 'high' ? 'text-orange-400' :
                    'text-[#0088EA]'
                  }`} />
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-[#0088EA]">{alert.symbol}</span>
                      <span className={`badge ${
                        alert.priority === 'critical' ? 'badge-red' :
                        alert.priority === 'high' ? 'badge-yellow' :
                        'badge-blue'
                      }`}>
                        {alert.priority}
                      </span>
                    </div>
                    <p className="text-[13px] text-[#44475B] leading-relaxed">{alert.message}</p>
                  </div>
                </div>
                {!alert.is_read && (
                  <button
                    onClick={() => onMarkRead(alert.id)}
                    className="shrink-0 p-1.5 text-[#A0A7B4] hover:text-[#0088EA] transition-colors rounded-lg hover:bg-[#0088EA]/5"
                    title="Mark as read"
                  >
                    <CheckCheck className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}