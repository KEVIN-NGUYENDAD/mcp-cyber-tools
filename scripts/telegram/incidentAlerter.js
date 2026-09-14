import fs from 'fs';
import path from 'path';
import { paths } from './paths.js';

class IncidentAlerter {
  constructor(alertDelivery) {
    this.alertDelivery = alertDelivery;
    this.processedIncidents = new Set();
    this.loadProcessedIncidents();
  }

  loadProcessedIncidents() {
    try {
      const processedPath = paths.processedIncidents;
      if (fs.existsSync(processedPath)) {
        const data = JSON.parse(fs.readFileSync(processedPath, 'utf8'));
        if (data.processed_ids) {
          data.processed_ids.forEach(id => this.processedIncidents.add(id));
        }
      }
    } catch (error) {
      console.error('Error loading processed incidents:', error);
    }
  }

  async checkAndAlertNewIncidents() {
    try {
      const incidentsPath = paths.incidents;
      if (!fs.existsSync(incidentsPath)) {
        console.log('No incidents file found');
        return [];
      }

      const data = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
      const incidents = data.incidents || [];
      const newIncidents = [];

      // Check for new incidents
      for (const incident of incidents) {
        if (!this.processedIncidents.has(incident.incident_id)) {
          newIncidents.push(incident);
        }
      }

      if (newIncidents.length === 0) {
        console.log('No new incidents to alert');
        return [];
      }

      // Sort by severity (CRITICAL first)
      const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
      newIncidents.sort((a, b) => {
        return (severityOrder[a.severity] || 999) - (severityOrder[b.severity] || 999);
      });

      // Sprint 11.3: mot lo su co -> MOT tin nhan.
      //
      // Vong lap cu gui mot tin cho moi su co. Bay su co thanh bay thong bao,
      // va nguoi truc ca cuon qua ca bay — ket qua la khong cai nao duoc doc ky.
      // Do khong phai loi cua Telegram: bay canh bao cung luc khong con la bay
      // tin hieu, no la mot tin hieu bi chia lam bay manh.
      //
      // Mot su co van di duong cu: gop mot thu lai khong phai gop, va no chi lam
      // mat cac nut thao tac day du cua canh bao don le.
      const results = [];
      if (newIncidents.length > 1) {
        console.log(`[ALERT] Gop ${newIncidents.length} su co thanh 1 Executive Alert`);
        const result = await this.alertDelivery.sendBatchedAlert(newIncidents);
        const ok = !!(result && result.success);
        for (const incident of newIncidents) {
          // Chi danh dau da xu ly khi gui THANH CONG. Danh dau khi that bai se
          // lam lo su co do bien mat vinh vien khoi moi lan chay sau.
          if (ok) this.processedIncidents.add(incident.incident_id);
          results.push({
            incident_id: incident.incident_id,
            threat_name: incident.title,
            severity: incident.severity,
            alerted: ok,
            batched: true,
            message_id: ok ? result.message_id : undefined,
            timestamp: ok ? result.timestamp : undefined,
            error: ok ? undefined : (result && result.error) || 'Khong gui duoc'
          });
        }
        if (ok) {
          console.log(`[SUCCESS] Executive Alert: msg_id=${result.message_id}, `
            + `${result.incident_ids.length} su co, ${result.skipped_duplicates || 0} trung bi bo`);
        }
      } else {
        for (const incident of newIncidents) {
          try {
            console.log(`[ALERT] Processing new incident: ${incident.incident_id}`);

            const result = await this.alertDelivery.sendIncidentAlert(incident);

            if (result && result.success) {
              this.processedIncidents.add(incident.incident_id);
              results.push({
                incident_id: incident.incident_id,
                threat_name: incident.title,
                severity: incident.severity,
                alerted: true,
                message_id: result.message_id,
                timestamp: result.timestamp
              });
              console.log(`[SUCCESS] Alert sent for ${incident.incident_id}: msg_id=${result.message_id}`);
            } else if (result) {
              results.push({
                incident_id: incident.incident_id,
                threat_name: incident.title,
                severity: incident.severity,
                alerted: false,
                error: result.error || 'Unknown error'
              });
              console.log(`[DEDUP] Alert already sent for ${incident.incident_id}`);
            }
          } catch (error) {
            console.error(`Error alerting incident ${incident.incident_id}:`, error);
            results.push({
              incident_id: incident.incident_id,
              threat_name: incident.title,
              severity: incident.severity,
              alerted: false,
              error: error.message
            });
          }
        }
      }

      // Save processed incidents
      this.saveProcessedIncidents();

      return results;
    } catch (error) {
      console.error('Error checking for new incidents:', error);
      return [];
    }
  }

  saveProcessedIncidents() {
    try {
      const processedPath = paths.processedIncidents;
      const data = {
        total_processed: this.processedIncidents.size,
        processed_ids: Array.from(this.processedIncidents),
        last_updated: new Date().toISOString()
      };

      fs.writeFileSync(processedPath, JSON.stringify(data, null, 2), 'utf8');
    } catch (error) {
      console.error('Error saving processed incidents:', error);
    }
  }

  async reprocessIncident(incidentId) {
    try {
      // Remove from processed set to allow resend
      this.processedIncidents.delete(incidentId);
      this.saveProcessedIncidents();

      // Get incident and resend
      const incident = this.getIncidentFromState(incidentId);
      if (!incident) {
        return {
          success: false,
          error: `Incident ${incidentId} not found`
        };
      }

      const result = await this.alertDelivery.sendIncidentAlert(incident);

      if (result && result.success) {
        this.processedIncidents.add(incidentId);
        this.saveProcessedIncidents();
      }

      return result;
    } catch (error) {
      console.error('Error reprocessing incident:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  getIncidentFromState(incidentId) {
    try {
      const incidentsPath = paths.incidents;
      if (!fs.existsSync(incidentsPath)) return null;

      const data = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
      const incidents = data.incidents || [];

      return incidents.find(i => i.id === incidentId) || null;
    } catch (error) {
      console.error('Error getting incident from state:', error);
      return null;
    }
  }

  getSummary() {
    try {
      const incidentsPath = paths.incidents;
      const historyPath = paths.notificationHistory;

      let totalIncidents = 0;
      let alertedCount = 0;

      if (fs.existsSync(incidentsPath)) {
        const data = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
        totalIncidents = (data.incidents || []).length;
      }

      if (fs.existsSync(historyPath)) {
        const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        alertedCount = history.total_alerts_sent || 0;
      }

      return {
        total_incidents: totalIncidents,
        total_alerted: alertedCount,
        processed: this.processedIncidents.size,
        pending: Math.max(0, totalIncidents - alertedCount)
      };
    } catch (error) {
      console.error('Error getting summary:', error);
      return null;
    }
  }
}

export default IncidentAlerter;
