import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { paths } from './paths.js';

class AlertDelivery {
  constructor(telegramBot) {
    this.telegramBot = telegramBot;
    this.antiSpamWindow = 30 * 60 * 1000; // 30 minutes
    this.sentAlerts = new Map();
    this.loadAlertHistory();
  }

  loadAlertHistory() {
    try {
      const historyPath = paths.notificationHistory;
      if (fs.existsSync(historyPath)) {
        const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        if (history.alerts) {
          history.alerts.forEach(alert => {
            const hash = this.generateHash(alert.incident_id);
            this.sentAlerts.set(hash, {
              timestamp: new Date(alert.timestamp),
              message_id: alert.message_id
            });
          });
        }
      }
    } catch (error) {
      console.error('Error loading alert history:', error);
    }
  }

  generateHash(incidentId) {
    return crypto.createHash('md5').update(incidentId).digest('hex');
  }

  isDeduplicatedAlert(incidentId) {
    const hash = this.generateHash(incidentId);
    const lastAlert = this.sentAlerts.get(hash);

    if (!lastAlert) return false;

    const timeSinceLastAlert = Date.now() - lastAlert.timestamp.getTime();
    return timeSinceLastAlert < this.antiSpamWindow;
  }

  async sendIncidentAlert(incident) {
    try {
      // Check for duplicate
      if (this.isDeduplicatedAlert(incident.incident_id)) {
        console.log(`[DEDUP] Alert for ${incident.incident_id} already sent within 30 minutes`);
        return null;
      }

      // Send alert with inline buttons
      const result = await this.telegramBot.sendAlertWithButtons(incident);

      if (result) {
        // Record in history
        this.recordAlertDelivery(incident, result.message_id);

        // Update sent alerts cache
        const hash = this.generateHash(incident.incident_id);
        this.sentAlerts.set(hash, {
          timestamp: new Date(),
          message_id: result.message_id
        });

        return {
          success: true,
          message_id: result.message_id,
          timestamp: new Date().toISOString(),
          incident_id: incident.incident_id
        };
      }
    } catch (error) {
      console.error('Error sending incident alert:', error);
      return {
        success: false,
        error: error.message,
        incident_id: incident.incident_id
      };
    }
  }

  async sendCriticalAlert(incident) {
    // Send immediately for CRITICAL incidents (bypass dedup for first CRITICAL)
    if (incident.severity === 'CRITICAL') {
      return this.sendIncidentAlert(incident);
    }
    return null;
  }

  recordAlertDelivery(incident, messageId) {
    try {
      const historyPath = paths.notificationHistory;
      let history = {
        total_alerts_sent: 0,
        alerts: []
      };

      if (fs.existsSync(historyPath)) {
        history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      }

      const alertEntry = {
        incident_id: incident.incident_id,
        threat_name: incident.threat_name,
        severity: incident.severity,
        timestamp: new Date().toISOString(),
        message_id: messageId,
        delivery_status: 'CONFIRMED',
        risk_score: incident.risk_score || 0
      };

      history.alerts.push(alertEntry);
      history.total_alerts_sent = history.alerts.length;
      history.last_alert = alertEntry;

      fs.writeFileSync(historyPath, JSON.stringify(history, null, 2), 'utf8');
    } catch (error) {
      console.error('Error recording alert delivery:', error);
    }
  }

  async resendAlert(incidentId) {
    try {
      const incident = this.getIncidentFromState(incidentId);
      if (!incident) {
        console.log(`Incident ${incidentId} not found`);
        return null;
      }

      // Force resend (ignore dedup)
      const result = await this.telegramBot.sendAlertWithButtons(incident);

      if (result) {
        this.recordAlertDelivery(incident, result.message_id);
        return {
          success: true,
          message_id: result.message_id
        };
      }
    } catch (error) {
      console.error('Error resending alert:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  getIncidentFromState(incidentId) {
    try {
      if (!fs.existsSync(paths.incidents)) return null;

      const data = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      const incidents = data.incidents || [];

      return incidents.find(i => i.id === incidentId) || null;
    } catch (error) {
      console.error('Error getting incident from state:', error);
      return null;
    }
  }

  getDeliveryStats() {
    try {
      const historyPath = paths.notificationHistory;
      if (!fs.existsSync(historyPath)) {
        return {
          total_sent: 0,
          by_severity: {
            CRITICAL: 0,
            HIGH: 0,
            MEDIUM: 0,
            LOW: 0
          },
          delivery_rate: 100
        };
      }

      const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      const stats = {
        total_sent: history.total_alerts_sent || 0,
        by_severity: {
          CRITICAL: 0,
          HIGH: 0,
          MEDIUM: 0,
          LOW: 0
        },
        delivery_rate: 100,
        last_alert: history.last_alert || null
      };

      if (history.alerts) {
        history.alerts.forEach(alert => {
          if (alert.severity && stats.by_severity[alert.severity] !== undefined) {
            stats.by_severity[alert.severity]++;
          }
        });
      }

      return stats;
    } catch (error) {
      console.error('Error getting delivery stats:', error);
      return null;
    }
  }

  clearDeduplicationCache(incidentId) {
    const hash = this.generateHash(incidentId);
    this.sentAlerts.delete(hash);
  }

  getAntiSpamStatus() {
    return {
      window_minutes: this.antiSpamWindow / 60000,
      active_dedup_count: this.sentAlerts.size,
      description: `Prevents duplicate alerts for same incident within ${this.antiSpamWindow / 60000} minutes`
    };
  }
}

export default AlertDelivery;
