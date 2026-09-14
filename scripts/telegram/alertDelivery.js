import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { paths } from './paths.js';

// Lich su canh bao tung mang ba ten cho cung mot mang: `sent_alerts` nam trong
// tep, `alerts` la noi lop nay ghi vao, `notifications` la noi bot doc ra. Ba
// ten thi hai trong ba luon rong — va mot lich su canh bao rong doc y het mot he
// thong chua tung canh bao gi.
//
// Ten chinh thuc: `sent_alerts`. Doc van chap nhan ca ba de lich su cu khong mat.
const ALERT_LIST_KEY = 'sent_alerts';

function alertList(history) {
  if (!history) return [];
  return history[ALERT_LIST_KEY] || history.alerts || history.notifications || [];
}

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
        {
          alertList(history).forEach(alert => {
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

  // Sprint 11.3: mot tin nhan cho ca lo, thay vi mot tin moi su co.
  //
  // Chong trung van tinh THEO TUNG su co: gop lo khong duoc phep gui lai mot su
  // co vua bao 10 phut truoc chi vi no di chung chuyen voi sau su co moi.
  async sendBatchedAlert(incidents) {
    const fresh = incidents.filter(i => !this.isDeduplicatedAlert(i.incident_id));
    const skipped = incidents.length - fresh.length;
    if (skipped) {
      console.log(`[DEDUP] ${skipped}/${incidents.length} su co da gui trong 30 phut, bo khoi lo`);
    }
    if (fresh.length === 0) return null;
    if (fresh.length === 1) {
      // Gop mot thu lai khong phai la gop — no chi lam mat cac nut thao tac day
      // du cua canh bao don le.
      return this.sendIncidentAlert(fresh[0]);
    }

    try {
      const result = await this.telegramBot.sendExecutiveAlert(fresh);
      if (!result) return null;

      // Ca lo dung chung mot message_id: do la su that, va lich su phai ghi
      // dung su that do de sau nay con truy nguoc duoc mot canh bao gop.
      for (const incident of fresh) {
        this.recordAlertDelivery(incident, result.message_id);
        this.sentAlerts.set(this.generateHash(incident.incident_id), {
          timestamp: new Date(),
          message_id: result.message_id
        });
      }

      return {
        success: true,
        batched: true,
        message_id: result.message_id,
        timestamp: new Date().toISOString(),
        incident_ids: fresh.map(i => i.incident_id),
        skipped_duplicates: skipped
      };
    } catch (error) {
      console.error('Error sending executive alert:', error);
      // Khong danh dau su co nao la da gui: lan chay sau phai thu lai duoc.
      return {
        success: false,
        batched: true,
        error: error.message,
        incident_ids: fresh.map(i => i.incident_id)
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
        [ALERT_LIST_KEY]: []
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

      const list = alertList(history);
      list.push(alertEntry);
      history[ALERT_LIST_KEY] = list;
      delete history.alerts;
      delete history.notifications;
      history.total_alerts_sent = list.length;
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

      {
        alertList(history).forEach(alert => {
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
