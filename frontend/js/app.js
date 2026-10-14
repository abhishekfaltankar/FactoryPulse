// FactoryPulse Frontend Application Logic
document.addEventListener("DOMContentLoaded", () => {
  // Navigation Tabs
  const navButtons = document.querySelectorAll(".nav-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      navButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetTab = btn.getAttribute("data-tab");
      document.getElementById(targetTab).classList.add("active");

      if (targetTab === "tab-telemetry") {
        updateTelemetryView();
      } else if (targetTab === "tab-ml") {
        loadModelMetadata();
      }
    });
  });

  // State
  let machines = [];
  let selectedMachineId = "CNC-101";
  let thermalChart = null;
  let mechanicalChart = null;

  // Toast notification helper
  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerText = message;
    if (type === "error") {
      toast.style.borderColor = "var(--accent-rose)";
    } else if (type === "success") {
      toast.style.borderColor = "var(--accent-emerald)";
    }
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // 1. Health & Fleet Overview
  async function checkBackendHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        document.getElementById("backend-status-text").innerText = "API Online";
        document.getElementById("backend-health-pill").style.borderColor = "rgba(16, 185, 129, 0.4)";
      }
    } catch (e) {
      document.getElementById("backend-status-text").innerText = "Offline";
      document.getElementById("backend-health-pill").style.borderColor = "rgba(239, 68, 68, 0.4)";
    }
  }

  async function loadFleetOverview() {
    try {
      const res = await fetch("/api/analytics/overview");
      if (res.ok) {
        const data = await res.json();
        document.getElementById("kpi-total-machines").innerText = data.total_machines;
        document.getElementById("kpi-avg-health").innerText = data.average_health_score + "%";
        document.getElementById("kpi-active-alerts").innerText = data.active_alerts_count;
        document.getElementById("kpi-risk-signals").innerText = data.predicted_failures_count;
      }
    } catch (e) {
      console.error("Failed to load fleet overview:", e);
    }
  }

  async function loadMachines() {
    try {
      const res = await fetch("/api/machines");
      if (res.ok) {
        machines = await res.json();
        renderMachinesGrid(machines);
        populateMachineSelects(machines);
      }
    } catch (e) {
      console.error("Failed to load machines:", e);
    }
  }

  function renderMachinesGrid(machineList) {
    const container = document.getElementById("fleet-machines-container");
    container.innerHTML = "";

    machineList.forEach(m => {
      const card = document.createElement("div");
      card.className = `glass-card machine-card status-${m.status}`;

      let healthColor = "var(--accent-emerald)";
      if (m.health_score < 60) healthColor = "var(--accent-rose)";
      else if (m.health_score < 80) healthColor = "var(--accent-amber)";

      card.innerHTML = `
        <div class="machine-head">
          <div>
            <div class="machine-id">${m.id}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">${m.name}</div>
          </div>
          <span class="machine-status-badge badge-${m.status}">${m.status}</span>
        </div>
        <div class="machine-meta">
          <div>Model: <strong>${m.model}</strong> (${m.machine_type}-Variant)</div>
          <div>Location: ${m.location}</div>
        </div>
        <div class="health-bar-container">
          <div class="health-bar-labels">
            <span>Operating Health</span>
            <strong style="color: ${healthColor};">${m.health_score.toFixed(1)}%</strong>
          </div>
          <div class="health-progress-track">
            <div class="health-progress-fill" style="width: ${m.health_score}%; background: ${healthColor};"></div>
          </div>
        </div>
        <div class="machine-card-actions">
          <button class="btn-secondary" onclick="inspectMachineTelemetry('${m.id}')">Inspect</button>
          <button class="btn-secondary" onclick="simulateMachine('${m.id}', '${m.machine_type}')">Simulate</button>
        </div>
      `;
      container.appendChild(card);
    });
  }

  function populateMachineSelects(machineList) {
    const selectTelemetry = document.getElementById("select-machine-telemetry");
    const selectMaint = document.getElementById("maint-machine-id");

    selectTelemetry.innerHTML = "";
    selectMaint.innerHTML = "";

    machineList.forEach(m => {
      const opt1 = document.createElement("option");
      opt1.value = m.id;
      opt1.innerText = `${m.id} - ${m.name}`;
      selectTelemetry.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = m.id;
      opt2.innerText = `${m.id} - ${m.name}`;
      selectMaint.appendChild(opt2);
    });

    selectTelemetry.value = selectedMachineId;
  }

  // Global triggers
  window.inspectMachineTelemetry = (id) => {
    selectedMachineId = id;
    document.getElementById("select-machine-telemetry").value = id;
    document.getElementById("btn-tab-telemetry").click();
  };

  window.simulateMachine = (id, type) => {
    document.getElementById("sim-machine-type").value = type;
    document.getElementById("btn-tab-simulator").click();
  };

  document.getElementById("select-machine-telemetry").addEventListener("change", (e) => {
    selectedMachineId = e.target.value;
    updateTelemetryView();
  });

  // 2. Machine Telemetry & Charts
  async function updateTelemetryView() {
    try {
      const res = await fetch(`/api/telemetry/${selectedMachineId}?limit=20`);
      if (res.ok) {
        const readings = await res.json();
        if (readings.length > 0) {
          const latest = readings[0];
          document.getElementById("live-air-temp").innerText = `${latest.air_temperature.toFixed(1)} K`;
          document.getElementById("live-air-celsius").innerText = `${(latest.air_temperature - 273.15).toFixed(1)} °C`;
          
          document.getElementById("live-proc-temp").innerText = `${latest.process_temperature.toFixed(1)} K`;
          const delta = latest.process_temperature - latest.air_temperature;
          document.getElementById("live-temp-delta").innerText = `Delta: ${delta.toFixed(1)} K`;

          document.getElementById("live-speed").innerText = `${latest.rotational_speed.toFixed(0)} RPM`;
          document.getElementById("live-torque").innerText = `${latest.torque.toFixed(1)} Nm`;

          const power = latest.torque * (latest.rotational_speed * 2.0 * Math.PI / 60.0);
          document.getElementById("live-calc-power").innerText = `Power: ${Math.round(power)} W`;

          renderTelemetryTable(readings);
          renderTelemetryCharts(readings);
        }
      }
    } catch (e) {
      console.error("Telemetry view error:", e);
    }
  }

  function renderTelemetryTable(readings) {
    const tbody = document.getElementById("telemetry-tbody");
    tbody.innerHTML = "";
    readings.slice(0, 10).forEach(r => {
      const tr = document.createElement("tr");
      const d = new Date(r.timestamp);
      tr.innerHTML = `
        <td>${d.toLocaleTimeString()}</td>
        <td>${r.air_temperature.toFixed(1)}</td>
        <td>${r.process_temperature.toFixed(1)}</td>
        <td>${r.rotational_speed.toFixed(0)}</td>
        <td>${r.torque.toFixed(1)}</td>
        <td>${r.tool_wear.toFixed(1)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderTelemetryCharts(readings) {
    const chronological = [...readings].reverse();
    const labels = chronological.map(r => new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    const airTemps = chronological.map(r => r.air_temperature);
    const procTemps = chronological.map(r => r.process_temperature);
    const speeds = chronological.map(r => r.rotational_speed);
    const torques = chronological.map(r => r.torque);

    // Thermal Chart
    const ctxThermal = document.getElementById("chart-thermal").getContext("2d");
    if (thermalChart) thermalChart.destroy();
    thermalChart = new Chart(ctxThermal, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Air Temp (K)",
            data: airTemps,
            borderColor: "#06b6d4",
            backgroundColor: "rgba(6, 182, 212, 0.1)",
            tension: 0.3,
            fill: true
          },
          {
            label: "Process Temp (K)",
            data: procTemps,
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.1)",
            tension: 0.3,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#94a3b8" } } },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } }
        }
      }
    });

    // Mechanical Chart
    const ctxMech = document.getElementById("chart-mechanical").getContext("2d");
    if (mechanicalChart) mechanicalChart.destroy();
    mechanicalChart = new Chart(ctxMech, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Speed (RPM)",
            data: speeds,
            borderColor: "#10b981",
            yAxisID: 'y',
            tension: 0.3
          },
          {
            label: "Torque (Nm)",
            data: torques,
            borderColor: "#ef4444",
            yAxisID: 'y1',
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#94a3b8" } } },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#10b981" }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: "#ef4444" }
          }
        }
      }
    });
  }

  // 3. Simulator Sliders & Inference
  const inputAirTemp = document.getElementById("input-air-temp");
  const inputProcTemp = document.getElementById("input-proc-temp");
  const inputSpeed = document.getElementById("input-rot-speed");
  const inputTorque = document.getElementById("input-torque");
  const inputToolWear = document.getElementById("input-tool-wear");

  function syncSliderDisplays() {
    document.getElementById("val-air-temp").innerText = `${parseFloat(inputAirTemp.value).toFixed(1)} K`;
    document.getElementById("val-proc-temp").innerText = `${parseFloat(inputProcTemp.value).toFixed(1)} K`;
    document.getElementById("val-rot-speed").innerText = `${parseInt(inputSpeed.value)} RPM`;
    document.getElementById("val-torque").innerText = `${parseFloat(inputTorque.value).toFixed(1)} Nm`;
    document.getElementById("val-tool-wear").innerText = `${parseInt(inputToolWear.value)} min`;

    // Derived preview
    const speed = parseFloat(inputSpeed.value);
    const torque = parseFloat(inputTorque.value);
    const pWatts = torque * (speed * 2.0 * Math.PI / 60.0);
    const delta = parseFloat(inputProcTemp.value) - parseFloat(inputAirTemp.value);
    const wearTorque = torque * parseFloat(inputToolWear.value);

    document.getElementById("sim-calc-power").innerText = `${Math.round(pWatts).toLocaleString()} W`;
    document.getElementById("sim-calc-delta").innerText = `${delta.toFixed(1)} K`;
    document.getElementById("sim-calc-wear-torque").innerText = `${Math.round(wearTorque).toLocaleString()} Nm·min`;
  }

  [inputAirTemp, inputProcTemp, inputSpeed, inputTorque, inputToolWear].forEach(input => {
    input.addEventListener("input", syncSliderDisplays);
  });
  syncSliderDisplays();

  // Presets
  document.getElementById("preset-normal").addEventListener("click", (e) => {
    e.preventDefault();
    inputAirTemp.value = 298.2;
    inputProcTemp.value = 308.7;
    inputSpeed.value = 1500;
    inputTorque.value = 40.0;
    inputToolWear.value = 20;
    syncSliderDisplays();
    executeInference();
  });

  document.getElementById("preset-hdf").addEventListener("click", (e) => {
    e.preventDefault();
    // HDF: Temp delta < 8.6K and Speed < 1380 RPM
    inputAirTemp.value = 302.0;
    inputProcTemp.value = 305.5; // delta 3.5K < 8.6K
    inputSpeed.value = 1250;     // < 1380 RPM
    inputTorque.value = 48.0;
    inputToolWear.value = 40;
    syncSliderDisplays();
    executeInference();
  });

  document.getElementById("preset-pwf").addEventListener("click", (e) => {
    e.preventDefault();
    // PWF: Power < 3500W or > 9000W
    inputAirTemp.value = 298.0;
    inputProcTemp.value = 308.0;
    inputSpeed.value = 2700;
    inputTorque.value = 90.0; // Power = 25,446 W >> 9000 W
    inputToolWear.value = 80;
    syncSliderDisplays();
    executeInference();
  });

  document.getElementById("preset-osf").addEventListener("click", (e) => {
    e.preventDefault();
    // OSF: Torque * Tool Wear exceeds limit
    inputAirTemp.value = 299.0;
    inputProcTemp.value = 309.5;
    inputSpeed.value = 1400;
    inputTorque.value = 75.0;
    inputToolWear.value = 220; // 75 * 220 = 16,500 > 12,000
    syncSliderDisplays();
    executeInference();
  });

  document.getElementById("preset-twf").addEventListener("click", (e) => {
    e.preventDefault();
    // TWF: Tool wear > 200 min
    inputAirTemp.value = 298.0;
    inputProcTemp.value = 308.0;
    inputSpeed.value = 1520;
    inputTorque.value = 44.0;
    inputToolWear.value = 240;
    syncSliderDisplays();
    executeInference();
  });

  document.getElementById("simulator-form").addEventListener("submit", (e) => {
    e.preventDefault();
    executeInference();
  });

  async function executeInference() {
    const payload = {
      machine_id: selectedMachineId,
      machine_type: document.getElementById("sim-machine-type").value,
      air_temperature: parseFloat(inputAirTemp.value),
      process_temperature: parseFloat(inputProcTemp.value),
      rotational_speed: parseFloat(inputSpeed.value),
      torque: parseFloat(inputTorque.value),
      tool_wear: parseFloat(inputToolWear.value)
    };

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        renderPredictionOutcome(data);
        showToast(`ML Prediction complete: ${data.risk_level} (${(data.failure_probability*100).toFixed(1)}%)`, data.risk_level === "CRITICAL" ? "error" : "success");
      }
    } catch (e) {
      console.error("Inference execution failed:", e);
      showToast("Prediction error", "error");
    }
  }

  function renderPredictionOutcome(pred) {
    const banner = document.getElementById("sim-risk-banner");
    banner.className = `risk-banner risk-${pred.risk_level}`;

    document.getElementById("sim-risk-title").innerText = `${pred.risk_level} STATUS`;
    document.getElementById("sim-failure-prob").innerText = `${(pred.failure_probability * 100).toFixed(1)}%`;
    document.getElementById("sim-failure-mode-text").innerText = `Failure Mode: ${pred.failure_mode}`;
    document.getElementById("sim-confidence").innerText = `${(pred.confidence_score * 100).toFixed(1)}%`;
    document.getElementById("sim-model-version").innerText = pred.model_version;

    const healthEstimate = Math.max(0, 100 - (pred.failure_probability * 100)).toFixed(1);
    document.getElementById("sim-health-score").innerText = `${healthEstimate}%`;
    const bar = document.getElementById("sim-health-bar");
    bar.style.width = `${healthEstimate}%`;
    if (healthEstimate < 60) bar.style.background = "var(--accent-rose)";
    else if (healthEstimate < 80) bar.style.background = "var(--accent-amber)";
    else bar.style.background = "var(--accent-emerald)";
  }

  // 4. ML Model Performance View
  async function loadModelMetadata() {
    try {
      const res = await fetch("/api/train/metadata");
      if (res.ok) {
        const data = await res.json();
        const m = data.metrics;
        document.getElementById("ml-stat-accuracy").innerText = `${(m.accuracy * 100).toFixed(1)}%`;
        document.getElementById("ml-stat-roc").innerText = m.roc_auc.toFixed(3);
        document.getElementById("ml-stat-recall").innerText = `${(m.recall * 100).toFixed(1)}%`;
        document.getElementById("ml-stat-f1").innerText = m.f1_score.toFixed(3);

        if (m.confusion_matrix) {
          document.getElementById("cm-tn").innerText = m.confusion_matrix[0][0].toLocaleString();
          document.getElementById("cm-fp").innerText = m.confusion_matrix[0][1].toLocaleString();
          document.getElementById("cm-fn").innerText = m.confusion_matrix[1][0].toLocaleString();
          document.getElementById("cm-tp").innerText = m.confusion_matrix[1][1].toLocaleString();
        }

        renderFeatureImportances(data.feature_importances);
      }
    } catch (e) {
      console.error("Failed to load model metadata:", e);
    }
  }

  function renderFeatureImportances(importances) {
    const container = document.getElementById("feature-importance-bars");
    container.innerHTML = "";

    const entries = Object.entries(importances).slice(0, 7);
    entries.forEach(([name, val]) => {
      const percent = (val * 100).toFixed(1);
      const row = document.createElement("div");
      row.style.marginBottom = "0.75rem";
      row.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 0.25rem;">
          <span style="color: var(--text-secondary);">${name.replace(/_/g, ' ')}</span>
          <strong style="color: var(--accent-cyan);">${percent}%</strong>
        </div>
        <div class="health-progress-track">
          <div class="health-progress-fill" style="width: ${percent}%; background: var(--accent-cyan);"></div>
        </div>
      `;
      container.appendChild(row);
    });
  }

  document.getElementById("btn-retrain-model").addEventListener("click", async () => {
    const btn = document.getElementById("btn-retrain-model");
    btn.disabled = true;
    btn.innerText = "⏳ Retraining Model...";
    showToast("Triggering full scikit-learn model retraining pipeline...", "info");

    try {
      const res = await fetch("/api/train", { method: "POST" });
      if (res.ok) {
        showToast("Model retraining completed successfully!", "success");
        loadModelMetadata();
      } else {
        showToast("Retraining failed.", "error");
      }
    } catch (e) {
      showToast("Retraining request failed", "error");
    } finally {
      btn.disabled = false;
      btn.innerText = "🔄 Retrain Model Pipeline";
    }
  });

  // 5. Alerts & Maintenance
  async function loadAlerts() {
    try {
      const res = await fetch("/api/alerts?limit=25");
      if (res.ok) {
        const alerts = await res.json();
        renderAlertsTable(alerts);
      }
    } catch (e) {
      console.error("Failed to load alerts:", e);
    }
  }

  function renderAlertsTable(alerts) {
    const tbody = document.getElementById("alerts-tbody");
    tbody.innerHTML = "";
    if (alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No active alerts.</td></tr>`;
      return;
    }

    alerts.forEach(a => {
      const tr = document.createElement("tr");
      let actionBtn = "";
      if (a.status === "ACTIVE") {
        actionBtn = `<button class="action-btn-sm" onclick="acknowledgeAlert(${a.id})">Acknowledge</button>`;
      } else if (a.status === "ACKNOWLEDGED") {
        actionBtn = `<button class="action-btn-sm" onclick="resolveAlert(${a.id})">Resolve</button>`;
      } else {
        actionBtn = `<span style="font-size: 0.72rem; color: var(--accent-emerald);">✓ Done</span>`;
      }

      tr.innerHTML = `
        <td><strong>${a.machine_id}</strong></td>
        <td><span class="machine-status-badge badge-${a.severity}">${a.severity}</span></td>
        <td style="font-size: 0.8rem;">${a.message}</td>
        <td>${a.status}</td>
        <td>${actionBtn}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  window.acknowledgeAlert = async (id) => {
    try {
      const res = await fetch(`/api/alerts/${id}/acknowledge`, { method: "PUT" });
      if (res.ok) {
        showToast(`Alert #${id} acknowledged`, "info");
        loadAlerts();
        loadFleetOverview();
      }
    } catch (e) {
      showToast("Failed to acknowledge alert", "error");
    }
  };

  window.resolveAlert = async (id) => {
    try {
      const res = await fetch(`/api/alerts/${id}/resolve`, { method: "PUT" });
      if (res.ok) {
        showToast(`Alert #${id} resolved`, "success");
        loadAlerts();
        loadFleetOverview();
      }
    } catch (e) {
      showToast("Failed to resolve alert", "error");
    }
  };

  async function loadMaintenance() {
    try {
      const res = await fetch("/api/maintenance?limit=25");
      if (res.ok) {
        const records = await res.json();
        renderMaintenanceTable(records);
      }
    } catch (e) {
      console.error("Failed to load maintenance records:", e);
    }
  }

  function renderMaintenanceTable(records) {
    const tbody = document.getElementById("maintenance-tbody");
    tbody.innerHTML = "";
    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No maintenance logs.</td></tr>`;
      return;
    }

    records.forEach(r => {
      const tr = document.createElement("tr");
      let actionBtn = "";
      if (r.status !== "COMPLETED") {
        actionBtn = `<button class="action-btn-sm" onclick="completeMaintenance(${r.id})">Complete</button>`;
      } else {
        actionBtn = `<span style="font-size: 0.72rem; color: var(--accent-emerald);">✓ Completed</span>`;
      }

      tr.innerHTML = `
        <td><strong>${r.machine_id}</strong></td>
        <td>${r.technician}</td>
        <td><span class="machine-status-badge badge-${r.status}">${r.status}</span></td>
        <td>$${r.cost.toFixed(2)}</td>
        <td>${actionBtn}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  window.completeMaintenance = async (id) => {
    try {
      const res = await fetch(`/api/maintenance/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "COMPLETED" })
      });
      if (res.ok) {
        showToast("Maintenance completed! Machine health restored to 100%.", "success");
        loadMaintenance();
        loadMachines();
        loadFleetOverview();
      }
    } catch (e) {
      showToast("Failed to complete maintenance", "error");
    }
  };

  // Maintenance Modal Form
  const modal = document.getElementById("modal-maintenance");
  document.getElementById("btn-open-maint-modal").addEventListener("click", () => {
    modal.style.display = "flex";
  });
  document.getElementById("btn-close-modal").addEventListener("click", () => {
    modal.style.display = "none";
  });

  document.getElementById("form-create-maintenance").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      machine_id: document.getElementById("maint-machine-id").value,
      technician: document.getElementById("maint-technician").value,
      cost: parseFloat(document.getElementById("maint-cost").value) || 0.0,
      notes: document.getElementById("maint-notes").value,
      status: "SCHEDULED"
    };

    try {
      const res = await fetch("/api/maintenance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showToast("Maintenance order scheduled successfully!", "success");
        modal.style.display = "none";
        loadMaintenance();
      }
    } catch (e) {
      showToast("Failed to schedule maintenance", "error");
    }
  });

  // Quick stream batch button
  document.getElementById("btn-quick-stream").addEventListener("click", async () => {
    const reading = {
      machine_id: selectedMachineId,
      air_temperature: 298.0 + (Math.random() * 2.0 - 1.0),
      process_temperature: 308.5 + (Math.random() * 2.0 - 1.0),
      rotational_speed: 1520 + (Math.random() * 60 - 30),
      torque: 40.0 + (Math.random() * 6 - 3),
      tool_wear: Math.floor(Math.random() * 50)
    };

    try {
      const res = await fetch("/api/telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reading)
      });
      if (res.ok) {
        showToast(`Ingested live telemetry reading for ${selectedMachineId}`, "success");
        updateTelemetryView();
        loadFleetOverview();
      }
    } catch (e) {
      showToast("Ingestion failed", "error");
    }
  });

  // Periodic polling every 8s
  setInterval(() => {
    loadFleetOverview();
    if (document.getElementById("tab-telemetry").classList.contains("active")) {
      updateTelemetryView();
    }
  }, 8000);

  // Initial Boot
  checkBackendHealth();
  loadFleetOverview();
  loadMachines();
  loadAlerts();
  loadMaintenance();
});
