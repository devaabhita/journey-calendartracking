/**
 * 🧭 Journey Tracker - Client-side Application (Calendar-first UI)
 */

const API_BASE = ""; // Relative path to FastAPI backend

const MONTH_NAMES_INDO = [
  "JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
  "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"
];

// Application State
const state = {
  activeTab: "tab-calendar",
  currentYear: new Date().getFullYear(),
  currentMonth: new Date().getMonth() + 1, // 1 - 12
  selectedDate: getTodayString(),
  calendarData: {},
  journeys: [],
  dayTasks: [],
  analyticsPeriod: "week",
  charts: {
    progress: null,
    category: null
  }
};

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function getTodayString() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateIndo(dateStr) {
  if (!dateStr) return "-";
  const [y, m, d] = dateStr.split("-").map(Number);
  const dateObj = new Date(y, m - 1, d);
  const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
  return dateObj.toLocaleDateString("id-ID", options);
}

function formatDayHeader(dateStr) {
  if (!dateStr) return "";
  const [y, m, d] = dateStr.split("-").map(Number);
  const dateObj = new Date(y, m - 1, d);
  const dayName = dateObj.toLocaleDateString("id-ID", { weekday: "long" }).toUpperCase();
  return `${dayName}, ${d} ${y}`;
}

function formatTime(timeStr) {
  if (!timeStr) return "";
  return timeStr.substring(0, 5); // HH:MM
}

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  const icon = type === "success" 
    ? '<i class="fa-solid fa-circle-check" style="color:#10b981;"></i>' 
    : type === "error" 
    ? '<i class="fa-solid fa-circle-exclamation" style="color:#ef4444;"></i>' 
    : '<i class="fa-solid fa-circle-info" style="color:#3b82f6;"></i>';

  toast.innerHTML = `${icon} <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ==========================================
// INITIALIZATION
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadAllInitialData();
});

function setupEventListeners() {
  // Navigation Tabs
  document.querySelectorAll(".nav-menu .nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Calendar Month Navigation
  document.getElementById("btn-prev-month").addEventListener("click", () => navigateMonth(-1));
  document.getElementById("btn-next-month").addEventListener("click", () => navigateMonth(1));
  document.getElementById("btn-current-month").addEventListener("click", () => {
    const now = new Date();
    state.currentYear = now.getFullYear();
    state.currentMonth = now.getMonth() + 1;
    state.selectedDate = getTodayString();
    loadCalendarMonth();
  });

  // Quick Action Buttons
  document.getElementById("btn-open-task-modal").addEventListener("click", () => openTaskModal());
  document.getElementById("btn-add-task-to-selected-day").addEventListener("click", () => openTaskModal(null, state.selectedDate));
  document.getElementById("btn-open-journey-modal")?.addEventListener("click", () => openJourneyModal());
  document.getElementById("btn-add-journey-hub")?.addEventListener("click", () => openJourneyModal());

  // Recurring Schedule Buttons
  document.getElementById("btn-open-recurring-modal").addEventListener("click", () => openRecurringModal());
  document.getElementById("btn-open-recurring-modal-top").addEventListener("click", () => openRecurringModal());

  // Popover detail button
  document.getElementById("btn-open-day-popover").addEventListener("click", () => openDayPopover(state.selectedDate));
  document.getElementById("btn-popover-add-task").addEventListener("click", () => {
    closeModal("modal-day-detail");
    openTaskModal(null, state.selectedDate);
  });

  // Close modals
  document.querySelectorAll("[data-close]").forEach(btn => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-close");
      closeModal(modalId);
    });
  });

  // Form Submissions
  document.getElementById("form-task").addEventListener("submit", handleTaskFormSubmit);
  document.getElementById("form-journey").addEventListener("submit", handleJourneyFormSubmit);
  document.getElementById("form-recurring").addEventListener("submit", handleRecurringFormSubmit);
  document.getElementById("form-daily-note")?.addEventListener("submit", handleDailyNoteSubmit);

  // Recurring Presets
  setupRecurringPresets();

  // Mood Selector Buttons
  document.querySelectorAll(".mood-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mood-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const moodVal = document.getElementById("note-mood-val");
      if (moodVal) moodVal.value = btn.getAttribute("data-mood");
    });
  });

  // Analytics Period Toggle
  document.querySelectorAll(".period-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".period-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.analyticsPeriod = btn.getAttribute("data-period");
      loadAnalyticsData();
    });
  });
}

function setupRecurringPresets() {
  const setDays = (arr) => {
    document.querySelectorAll("input[name='rec-day']").forEach(cb => {
      cb.checked = arr.includes(parseInt(cb.value, 10));
    });
  };

  document.getElementById("btn-shortcut-senin-rabu").addEventListener("click", () => setDays([0, 1, 2]));
  document.getElementById("btn-shortcut-weekdays").addEventListener("click", () => setDays([0, 1, 2, 3, 4]));
  document.getElementById("btn-shortcut-everyday").addEventListener("click", () => setDays([0, 1, 2, 3, 4, 5, 6]));
  document.getElementById("btn-shortcut-weekend").addEventListener("click", () => setDays([5, 6]));

  // Date duration presets
  document.getElementById("btn-dur-1w").addEventListener("click", () => {
    const start = new Date(state.selectedDate || getTodayString());
    const end = new Date(start);
    end.setDate(end.getDate() + 6);
    document.getElementById("rec-start-date").value = formatDateInput(start);
    document.getElementById("rec-end-date").value = formatDateInput(end);
  });

  document.getElementById("btn-dur-2w").addEventListener("click", () => {
    const start = new Date(state.selectedDate || getTodayString());
    const end = new Date(start);
    end.setDate(end.getDate() + 13);
    document.getElementById("rec-start-date").value = formatDateInput(start);
    document.getElementById("rec-end-date").value = formatDateInput(end);
  });

  document.getElementById("btn-dur-1m").addEventListener("click", () => {
    const start = new Date(state.currentYear, state.currentMonth - 1, 1);
    const end = new Date(state.currentYear, state.currentMonth, 0);
    document.getElementById("rec-start-date").value = formatDateInput(start);
    document.getElementById("rec-end-date").value = formatDateInput(end);
  });
}

function formatDateInput(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll(".nav-menu .nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(pane => {
    pane.classList.toggle("active", pane.id === tabId);
  });

  if (tabId === "tab-calendar") {
    loadCalendarMonth();
  } else if (tabId === "tab-journeys") {
    loadJourneys();
  } else if (tabId === "tab-analytics") {
    loadAnalyticsData();
  } else if (tabId === "tab-reflections") {
    loadTodayReflection();
    loadReflectionHistory();
  }
}

function navigateMonth(delta) {
  let newMonth = state.currentMonth + delta;
  let newYear = state.currentYear;

  if (newMonth < 1) {
    newMonth = 12;
    newYear -= 1;
  } else if (newMonth > 12) {
    newMonth = 1;
    newYear += 1;
  }

  state.currentYear = newYear;
  state.currentMonth = newMonth;
  loadCalendarMonth();
}

// ==========================================
// DATA FETCHING & RENDERING
// ==========================================

async function loadAllInitialData() {
  await Promise.all([
    loadJourneys(),
    loadGlobalStats(),
    loadCalendarMonth(),
    loadTodayReflection()
  ]);
}

// 1. STATS & METRICS
async function loadGlobalStats() {
  try {
    const [streakRes, summaryRes] = await Promise.all([
      fetch(`${API_BASE}/stats/streak`),
      fetch(`${API_BASE}/stats/summary?period=week`)
    ]);

    if (streakRes.ok) {
      const streakData = await streakRes.json();
      document.getElementById("sidebar-current-streak").textContent = `${streakData.current_streak} Hari`;
      document.getElementById("sidebar-longest-streak").textContent = `${streakData.longest_streak} Hari`;
      document.getElementById("streak-circle-val").textContent = streakData.current_streak;
    }

    if (summaryRes.ok) {
      const summaryData = await summaryRes.json();
      // Update the "INFORMASI RIWAYAT JOURNEY TRACKING SINGKAT" pill
      updateJourneySummaryPill(summaryData);
    }
  } catch (err) {
    console.error("Error loading global stats:", err);
  }
}

function updateJourneySummaryPill(summary) {
  const pillContent = document.getElementById("pill-content-text");
  if (!pillContent) return;

  const activeJourneysCount = state.journeys.length;
  pillContent.textContent = `${activeJourneysCount} Journey Aktif • ${summary.progress_percent}% Selesai Pekan Ini (${summary.completed_tasks}/${summary.total_tasks} Task) • ${summary.total_focus_hours} Jam Fokus`;
}

// 2. CALENDAR MONTH VIEW (GRID)
async function loadCalendarMonth() {
  const monthName = MONTH_NAMES_INDO[state.currentMonth - 1];
  document.getElementById("calendar-month-heading").textContent = monthName;
  document.getElementById("calendar-year-heading").textContent = state.currentYear;

  try {
    const res = await fetch(`${API_BASE}/stats/calendar?year=${state.currentYear}&month=${state.currentMonth}`);
    if (!res.ok) throw new Error("Gagal mengambil data kalender");
    const data = await res.json();
    state.calendarData = data.days || {};

    renderCalendarGrid();
    renderDayPanel(state.selectedDate);
  } catch (err) {
    console.error("Error loading calendar month:", err);
    showToast("Gagal memuat kalender: " + err.message, "error");
  }
}

function renderCalendarGrid() {
  const grid = document.getElementById("calendar-days-grid");
  grid.innerHTML = "";

  const year = state.currentYear;
  const month = state.currentMonth;

  // First day of this month
  const firstDayObj = new Date(year, month - 1, 1);
  const startDayOfWeek = firstDayObj.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday

  // Total days in current month
  const daysInCurrentMonth = new Date(year, month, 0).getDate();

  // Total days in previous month
  const daysInPrevMonth = new Date(year, month - 1, 0).getDate();

  const todayStr = getTodayString();

  // 1. Cells for previous month days to align column
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    const dayNum = daysInPrevMonth - i;
    const prevCell = document.createElement("div");
    prevCell.className = "calendar-cell other-month";
    prevCell.innerHTML = `
      <div class="cell-top-row">
        <span class="cell-date-num">${dayNum}</span>
      </div>
    `;
    grid.appendChild(prevCell);
  }

  // 2. Cells for current month days
  for (let day = 1; day <= daysInCurrentMonth; day++) {
    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const dayOfWeek = new Date(year, month - 1, day).getDay();

    const isSunday = (dayOfWeek === 0);
    const isSaturday = (dayOfWeek === 6);
    const isToday = (dateStr === todayStr);
    const isSelected = (dateStr === state.selectedDate);

    const dayData = state.calendarData[dateStr] || { total: 0, completed: 0, progress_percent: 0 };
    const total = dayData.total;
    const completed = dayData.completed;
    const progress = dayData.progress_percent;

    const cell = document.createElement("div");
    let cellClasses = ["calendar-cell"];
    if (isSunday) cellClasses.push("is-sunday");
    if (isSaturday) cellClasses.push("is-saturday");
    if (isToday) cellClasses.push("is-today");
    if (isSelected) cellClasses.push("selected");

    cell.className = cellClasses.join(" ");
    cell.setAttribute("data-date", dateStr);

    // Progress under date number
    let progressHtml = "";
    if (total > 0) {
      const isDoneAll = (completed === total && total > 0);
      progressHtml = `
        <div class="cell-progress-bar-wrap">
          <div class="cell-progress-label">
            <span class="cell-progress-pct ${isDoneAll ? 'done-all' : ''}">${progress}%</span>
            <span>${completed}/${total}</span>
          </div>
          <div class="cell-mini-track">
            <div class="cell-mini-fill ${isDoneAll ? 'complete' : ''}" style="width: ${progress}%"></div>
          </div>
        </div>
      `;
    } else {
      progressHtml = `
        <div class="cell-progress-bar-wrap">
          <div class="cell-empty-dot">-</div>
        </div>
      `;
    }

    cell.innerHTML = `
      <div class="cell-top-row">
        <span class="cell-date-num">${day}</span>
        ${total > 0 ? `<span class="cell-task-counter">${total} task</span>` : ''}
      </div>
      ${progressHtml}
    `;

    // Click handler to select day and show tasks
    cell.addEventListener("click", () => {
      selectCalendarDate(dateStr);
    });

    // Double click to open popup modal like in the bottom sketch
    cell.addEventListener("dblclick", () => {
      openDayPopover(dateStr);
    });

    grid.appendChild(cell);
  }

  // 3. Cells for next month days to complete 7-column grid
  const totalCellsRendered = startDayOfWeek + daysInCurrentMonth;
  const nextMonthCellsNeeded = (7 - (totalCellsRendered % 7)) % 7;
  for (let d = 1; d <= nextMonthCellsNeeded; d++) {
    const nextCell = document.createElement("div");
    nextCell.className = "calendar-cell other-month";
    nextCell.innerHTML = `
      <div class="cell-top-row">
        <span class="cell-date-num">${d}</span>
      </div>
    `;
    grid.appendChild(nextCell);
  }
}

function selectCalendarDate(dateStr) {
  state.selectedDate = dateStr;

  // Highlight selected cell in calendar
  document.querySelectorAll(".calendar-cell").forEach(cell => {
    cell.classList.toggle("selected", cell.getAttribute("data-date") === dateStr);
  });

  renderDayPanel(dateStr);
}

// 3. RIGHT PANEL ("HARI INI / TANGGAL TERPILIH")
function renderDayPanel(dateStr) {
  const isToday = (dateStr === getTodayString());
  const headline = document.getElementById("panel-day-headline");
  const fullDateText = document.getElementById("panel-date-full");

  headline.textContent = isToday ? "Hari ini:" : "Kegiatan Tanggal:";
  fullDateText.textContent = formatDateIndo(dateStr);

  const dayData = state.calendarData[dateStr] || { total: 0, completed: 0, progress_percent: 0, tasks: [] };
  const total = dayData.total;
  const completed = dayData.completed;
  const progress = dayData.progress_percent;

  // Update Progress Bar
  document.getElementById("panel-day-progress-pct").textContent = `${progress}% (${completed}/${total} selesai)`;
  document.getElementById("panel-day-progress-bar").style.width = `${progress}%`;
  document.getElementById("panel-task-count").textContent = `${total} Kegiatan`;

  // Render Tasks List
  const container = document.getElementById("panel-tasks-list");
  if (!dayData.tasks || dayData.tasks.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="padding: 2rem 1rem;">
        <i class="fa-solid fa-calendar-check" style="font-size: 2rem; color: var(--text-subtle); margin-bottom: 0.5rem;"></i>
        <p style="font-size: 0.85rem;">Belum ada kegiatan dijadwalkan.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = dayData.tasks.map(t => {
    const statusClass = t.is_done ? "selesai" : "belum";
    const statusText = t.is_done ? "SELESAI" : "BELUM";
    const timeDisplay = (t.start_time || t.end_time)
      ? `${formatTime(t.start_time)} - ${formatTime(t.end_time)}`
      : "";

    return `
      <div class="panel-task-item ${t.is_done ? 'completed' : ''}">
        <input 
          type="checkbox" 
          class="task-checkbox" 
          ${t.is_done ? 'checked' : ''} 
          onchange="toggleTaskFromCalendar(${t.id})"
        >
        <div class="panel-task-info">
          <div class="p-task-title">${escapeHtml(t.title)}</div>
          <div class="p-task-meta">
            <span><i class="fa-solid fa-route"></i> ${escapeHtml(t.journey_title || 'Journey')}</span>
            ${timeDisplay ? `<span>• <i class="fa-regular fa-clock"></i> ${timeDisplay}</span>` : ''}
          </div>
        </div>
        <span class="p-status-badge ${statusClass}">${statusText}</span>
        <button class="btn-icon btn-sm" onclick="editTask(${t.id})" title="Edit">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button class="btn-icon btn-sm" onclick="deleteTask(${t.id}, '${escapeJs(t.title)}')" title="Hapus">
          <i class="fa-solid fa-trash-can" style="color:#ef4444;"></i>
        </button>
      </div>
    `;
  }).join("");
}

// 4. DAY DETAIL POPOVER MODAL (PERSIS SKETSA BAWAH)
function openDayPopover(dateStr) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const monthName = MONTH_NAMES_INDO[m - 1];

  document.getElementById("popover-header-month").textContent = monthName;
  document.getElementById("popover-header-day").textContent = formatDayHeader(dateStr);

  const dayData = state.calendarData[dateStr] || { total: 0, completed: 0, progress_percent: 0, tasks: [] };
  const container = document.getElementById("popover-tasks-list");

  if (!dayData.tasks || dayData.tasks.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding: 2rem 1rem; color: #94a3b8; font-size: 0.88rem;">
        Tidak ada kegiatan pada tanggal ini.
      </div>
    `;
  } else {
    container.innerHTML = dayData.tasks.map(t => {
      const statusClass = t.is_done ? "selesai" : "belum";
      const statusText = t.is_done ? "SELESAI" : "BELUM";

      return `
        <div class="popover-task-row ${t.is_done ? 'done' : ''}">
          <div class="popover-task-left">
            <input 
              type="checkbox" 
              class="task-checkbox" 
              ${t.is_done ? 'checked' : ''} 
              onchange="toggleTaskFromPopover(${t.id})"
            >
            <span class="popover-task-text">• ${escapeHtml(t.title)}</span>
          </div>
          <span class="p-status-badge ${statusClass}">${statusText}</span>
        </div>
      `;
    }).join("");
  }

  openModal("modal-day-detail");
}

async function toggleTaskFromCalendar(taskId) {
  await toggleTaskStatus(taskId);
}

async function toggleTaskFromPopover(taskId) {
  await toggleTaskStatus(taskId);
  // Re-render popover content
  openDayPopover(state.selectedDate);
}

async function toggleTaskStatus(taskId) {
  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/toggle`, {
      method: "PATCH"
    });
    if (!res.ok) throw new Error("Gagal mengubah status tugas");
    const updated = await res.json();

    showToast(
      updated.is_done ? "🎉 Task selesai! Progres tercatat." : "Status dikembalikan ke belum selesai.",
      "success"
    );

    // Refresh calendar & global metrics
    await Promise.all([
      loadCalendarMonth(),
      loadJourneys(),
      loadGlobalStats()
    ]);
  } catch (err) {
    console.error("Error toggling task:", err);
    showToast("Gagal mengubah status: " + err.message, "error");
    loadCalendarMonth();
  }
}

// 5. JOURNEYS
async function loadJourneys() {
  try {
    const res = await fetch(`${API_BASE}/journeys`);
    if (!res.ok) throw new Error("Gagal mengambil data journeys");
    const data = await res.json();
    state.journeys = data;

    document.getElementById("nav-journey-count").textContent = data.length;
    populateJourneyDropdowns(data);
    renderJourneysGrid(data);

    // Update pill text as well
    const summaryRes = await fetch(`${API_BASE}/stats/summary?period=week`);
    if (summaryRes.ok) {
      const summary = await summaryRes.json();
      updateJourneySummaryPill(summary);
    }
  } catch (err) {
    console.error("Error loading journeys:", err);
  }
}

function populateJourneyDropdowns(journeys) {
  const taskModalSelect = document.getElementById("task-journey-id");
  const recModalSelect = document.getElementById("rec-journey-id");

  taskModalSelect.innerHTML = '<option value="" disabled selected>Pilih Journey Tujuan</option>';
  recModalSelect.innerHTML = '<option value="" disabled selected>Pilih Journey Tujuan</option>';

  journeys.forEach(j => {
    const opt1 = document.createElement("option");
    opt1.value = j.id;
    opt1.textContent = j.title;
    taskModalSelect.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = j.id;
    opt2.textContent = j.title;
    recModalSelect.appendChild(opt2);
  });
}

function renderJourneysGrid(journeys) {
  const grid = document.getElementById("journeys-grid");
  if (!grid) return;

  if (!journeys || journeys.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="fa-solid fa-compass"></i>
        <p>Belum ada Journey dibuat. Mulai langkah pertamamu sekarang!</p>
        <button class="btn btn-primary" onclick="openJourneyModal()">
          <i class="fa-solid fa-plus"></i> Buat Journey Pertama
        </button>
      </div>
    `;
    return;
  }

  grid.innerHTML = journeys.map(j => {
    return `
      <div class="journey-card">
        <div class="journey-card-header">
          <div class="journey-title">${escapeHtml(j.title)}</div>
          <div class="journey-actions">
            <button class="btn-icon btn-sm" onclick="editJourney(${j.id})" title="Edit Journey">
              <i class="fa-solid fa-pen"></i>
            </button>
            <button class="btn-icon btn-sm" onclick="deleteJourney(${j.id}, '${escapeJs(j.title)}')" title="Hapus Journey">
              <i class="fa-solid fa-trash-can" style="color:#ef4444;"></i>
            </button>
          </div>
        </div>

        <p class="journey-desc">${escapeHtml(j.description || "Tidak ada deskripsi.")}</p>

        <div class="journey-progress-wrap">
          <div class="progress-info">
            <span>Progres: <strong>${j.progress_percent}%</strong></span>
            <span>${j.completed_tasks} / ${j.total_tasks} selesai</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: ${j.progress_percent}%"></div>
          </div>
        </div>

        <div class="journey-footer">
          <span><i class="fa-regular fa-calendar"></i> ${j.start_date} ${j.target_date ? 's.d. ' + j.target_date : ''}</span>
          <button class="btn btn-sm btn-ghost" onclick="openTaskModalForJourney(${j.id})" style="color:var(--accent-primary);">
            <i class="fa-solid fa-plus"></i> Tambah Task
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// ==========================================
// MODAL & FORM OPERATIONS
// ==========================================

function openModal(modalId) {
  document.getElementById(modalId).classList.add("open");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("open");
}

// 1. RECURRING SCHEDULE MODAL
function openRecurringModal() {
  const form = document.getElementById("form-recurring");
  form.reset();

  // Set default dates: today to +6 days
  const today = new Date();
  const nextWeek = new Date();
  nextWeek.setDate(today.getDate() + 6);

  document.getElementById("rec-start-date").value = formatDateInput(today);
  document.getElementById("rec-end-date").value = formatDateInput(nextWeek);
  document.getElementById("rec-start-time").value = "19:00";
  document.getElementById("rec-end-time").value = "20:30";

  // Select first journey if available
  if (state.journeys.length > 0) {
    document.getElementById("rec-journey-id").value = state.journeys[0].id;
  }

  // Default days: Senin, Selasa, Rabu
  document.querySelectorAll("input[name='rec-day']").forEach(cb => {
    cb.checked = ["0", "1", "2"].includes(cb.value);
  });

  openModal("modal-recurring");
}

async function handleRecurringFormSubmit(e) {
  e.preventDefault();
  const journeyId = parseInt(document.getElementById("rec-journey-id").value, 10);
  const title = document.getElementById("rec-title").value.trim();
  const category = document.getElementById("rec-category").value.trim() || "General";
  const priority = parseInt(document.getElementById("rec-priority").value, 10);
  const startTime = document.getElementById("rec-start-time").value || null;
  const endTime = document.getElementById("rec-end-time").value || null;
  const startDate = document.getElementById("rec-start-date").value;
  const endDate = document.getElementById("rec-end-date").value;

  const selectedDays = [];
  document.querySelectorAll("input[name='rec-day']:checked").forEach(cb => {
    selectedDays.push(parseInt(cb.value, 10));
  });

  if (selectedDays.length === 0) {
    showToast("Pilih minimal satu hari dalam seminggu!", "error");
    return;
  }

  const payload = {
    journey_id: journeyId,
    title,
    category,
    priority,
    start_time: startTime ? `${startTime}:00` : null,
    end_time: endTime ? `${endTime}:00` : null,
    days_of_week: selectedDays,
    start_date: startDate,
    end_date: endDate
  };

  try {
    const res = await fetch(`${API_BASE}/tasks/recurring`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Gagal membuat jadwal berulang");
    }

    const createdTasks = await res.json();
    closeModal("modal-recurring");
    showToast(`✨ Berhasil menjadwalkan ${createdTasks.length} kegiatan ke kalender!`, "success");

    await Promise.all([
      loadCalendarMonth(),
      loadJourneys(),
      loadGlobalStats()
    ]);
  } catch (err) {
    showToast("Error: " + err.message, "error");
  }
}

// 2. SINGLE TASK MODAL
function openTaskModal(taskId = null, targetDate = null) {
  const form = document.getElementById("form-task");
  form.reset();
  document.getElementById("task-id").value = "";
  document.getElementById("modal-task-title").innerHTML = '<i class="fa-solid fa-list-check"></i> Tambah Kegiatan Baru';
  document.getElementById("btn-save-task").textContent = "Simpan Kegiatan";

  document.getElementById("task-date").value = targetDate || state.selectedDate;
  document.getElementById("task-repeat").value = "none";
  document.getElementById("task-priority").value = "2";

  if (state.journeys.length > 0) {
    document.getElementById("task-journey-id").value = state.journeys[0].id;
  }

  if (taskId) {
    // Find task from calendar data
    let foundTask = null;
    for (const d in state.calendarData) {
      const t = (state.calendarData[d].tasks || []).find(item => item.id === taskId);
      if (t) { foundTask = t; break; }
    }

    if (foundTask) {
      document.getElementById("task-id").value = foundTask.id;
      document.getElementById("modal-task-title").innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Edit Kegiatan';
      document.getElementById("btn-save-task").textContent = "Update Kegiatan";
      document.getElementById("task-journey-id").value = foundTask.journey_id;
      document.getElementById("task-title").value = foundTask.title;
      document.getElementById("task-category").value = foundTask.category || "";
      document.getElementById("task-priority").value = foundTask.priority || 2;
      document.getElementById("task-date").value = foundTask.task_date;
      document.getElementById("task-repeat").value = foundTask.repeat_rule || "none";
      document.getElementById("task-start-time").value = foundTask.start_time ? foundTask.start_time.substring(0, 5) : "";
      document.getElementById("task-end-time").value = foundTask.end_time ? foundTask.end_time.substring(0, 5) : "";
    }
  }

  openModal("modal-task");
}

function openTaskModalForJourney(journeyId) {
  openTaskModal();
  document.getElementById("task-journey-id").value = journeyId;
}

function editTask(taskId) {
  openTaskModal(taskId);
}

async function handleTaskFormSubmit(e) {
  e.preventDefault();
  const taskId = document.getElementById("task-id").value;
  const journeyId = parseInt(document.getElementById("task-journey-id").value, 10);
  const title = document.getElementById("task-title").value.trim();
  const category = document.getElementById("task-category").value.trim() || "General";
  const priority = parseInt(document.getElementById("task-priority").value, 10);
  const taskDate = document.getElementById("task-date").value;
  const repeatRule = document.getElementById("task-repeat").value;
  const startTime = document.getElementById("task-start-time").value || null;
  const endTime = document.getElementById("task-end-time").value || null;

  const payload = {
    journey_id: journeyId,
    title,
    category,
    priority,
    task_date: taskDate,
    repeat_rule: repeatRule,
    start_time: startTime ? `${startTime}:00` : null,
    end_time: endTime ? `${endTime}:00` : null
  };

  try {
    let res;
    if (taskId) {
      res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Gagal menyimpan tugas");
    }

    closeModal("modal-task");
    showToast(taskId ? "Kegiatan berhasil diupdate!" : "Kegiatan baru berhasil ditambahkan!", "success");

    await Promise.all([
      loadCalendarMonth(),
      loadJourneys(),
      loadGlobalStats()
    ]);
  } catch (err) {
    showToast("Error: " + err.message, "error");
  }
}

async function deleteTask(taskId, taskTitle) {
  if (!confirm(`Hapus kegiatan "${taskTitle}"?`)) return;

  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Gagal menghapus tugas");

    showToast("Kegiatan telah dihapus.", "info");
    await Promise.all([
      loadCalendarMonth(),
      loadJourneys(),
      loadGlobalStats()
    ]);
  } catch (err) {
    showToast("Gagal menghapus: " + err.message, "error");
  }
}

// 3. JOURNEY MODAL
function openJourneyModal(journeyId = null) {
  const form = document.getElementById("form-journey");
  form.reset();
  document.getElementById("journey-id").value = "";
  document.getElementById("modal-journey-title").innerHTML = '<i class="fa-solid fa-route"></i> Tambah Journey Baru';
  document.getElementById("btn-save-journey").textContent = "Simpan Journey";
  document.getElementById("journey-start-date").value = getTodayString();

  if (journeyId) {
    const journey = state.journeys.find(j => j.id === journeyId);
    if (journey) {
      document.getElementById("journey-id").value = journey.id;
      document.getElementById("modal-journey-title").innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Edit Journey';
      document.getElementById("btn-save-journey").textContent = "Update Journey";
      document.getElementById("journey-title").value = journey.title;
      document.getElementById("journey-desc").value = journey.description || "";
      document.getElementById("journey-start-date").value = journey.start_date;
      document.getElementById("journey-target-date").value = journey.target_date || "";
    }
  }

  openModal("modal-journey");
}

function editJourney(journeyId) {
  openJourneyModal(journeyId);
}

async function handleJourneyFormSubmit(e) {
  e.preventDefault();
  const journeyId = document.getElementById("journey-id").value;
  const title = document.getElementById("journey-title").value.trim();
  const description = document.getElementById("journey-desc").value.trim();
  const startDate = document.getElementById("journey-start-date").value;
  const targetDate = document.getElementById("journey-target-date").value || null;

  const payload = {
    title,
    description,
    start_date: startDate,
    target_date: targetDate
  };

  try {
    let res;
    if (journeyId) {
      res = await fetch(`${API_BASE}/journeys/${journeyId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch(`${API_BASE}/journeys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Gagal menyimpan journey");
    }

    closeModal("modal-journey");
    showToast(journeyId ? "Journey berhasil diupdate!" : "Journey baru berhasil dibuat!", "success");

    await loadJourneys();
  } catch (err) {
    showToast("Error: " + err.message, "error");
  }
}

async function deleteJourney(journeyId, journeyTitle) {
  if (!confirm(`Hapus journey "${journeyTitle}"? Seluruh kegiatan di dalamnya juga akan terhapus.`)) return;

  try {
    const res = await fetch(`${API_BASE}/journeys/${journeyId}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Gagal menghapus journey");

    showToast("Journey telah dihapus.", "info");
    await Promise.all([
      loadJourneys(),
      loadCalendarMonth(),
      loadGlobalStats()
    ]);
  } catch (err) {
    showToast("Gagal menghapus: " + err.message, "error");
  }
}

// ==========================================
// ANALYTICS & REKAP TAB
// ==========================================

async function loadAnalyticsData() {
  await Promise.all([
    renderHeatmap(),
    loadSummaryAndProgressChart(),
    loadCategoryChart()
  ]);
}

async function renderHeatmap() {
  const grid = document.getElementById("heatmap-grid");
  if (!grid) return;

  try {
    const res = await fetch(`${API_BASE}/stats/heatmap?days=60`);
    if (!res.ok) throw new Error("Gagal memuat data heatmap");
    const data = await res.json();

    grid.innerHTML = data.days.map(d => {
      let level = 0;
      if (d.completed >= 4) level = 4;
      else if (d.completed === 3) level = 3;
      else if (d.completed === 2) level = 2;
      else if (d.completed === 1) level = 1;

      return `
        <div 
          class="heat-cell lvl-${level}" 
          title="${d.date}: ${d.completed} selesai dari ${d.total} kegiatan"
          onclick="jumpToDateFromHeatmap('${d.date}')"
        ></div>
      `;
    }).join("");
  } catch (err) {
    console.error("Heatmap error:", err);
  }
}

function jumpToDateFromHeatmap(dateStr) {
  state.selectedDate = dateStr;
  const [y, m, d] = dateStr.split("-").map(Number);
  state.currentYear = y;
  state.currentMonth = m;

  switchTab("tab-calendar");
  loadCalendarMonth();
  showToast(`Menampilkan tanggal ${dateStr}`, "info");
}

async function loadSummaryAndProgressChart() {
  const canvas = document.getElementById("tasksProgressChart");
  if (!canvas) return;

  try {
    const res = await fetch(`${API_BASE}/stats/summary?period=${state.analyticsPeriod}`);
    if (!res.ok) return;
    const summary = await res.json();

    const ctx = canvas.getContext("2d");
    if (state.charts.progress) {
      state.charts.progress.destroy();
    }

    state.charts.progress = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Total Kegiatan", "Selesai Dikerjakan", "Jam Fokus (h)"],
        datasets: [{
          label: `Rekap ${state.analyticsPeriod === 'week' ? 'Mingguan' : 'Bulanan'}`,
          data: [summary.total_tasks, summary.completed_tasks, summary.total_focus_hours],
          backgroundColor: [
            "rgba(99, 102, 241, 0.7)",
            "rgba(16, 185, 129, 0.7)",
            "rgba(245, 158, 11, 0.7)"
          ],
          borderColor: [
            "#6366f1",
            "#10b981",
            "#f59e0b"
          ],
          borderWidth: 1.5,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: "rgba(255, 255, 255, 0.06)" },
            ticks: { color: "#9ca3af" }
          },
          x: {
            grid: { display: false },
            ticks: { color: "#9ca3af" }
          }
        }
      }
    });
  } catch (err) {
    console.error("Chart error:", err);
  }
}

async function loadCategoryChart() {
  const canvas = document.getElementById("categoryDistributionChart");
  if (!canvas) return;

  try {
    const res = await fetch(`${API_BASE}/stats/categories`);
    if (!res.ok) return;
    const categories = await res.json();

    const labels = categories.map(c => c.category);
    const dataCounts = categories.map(c => c.total);

    const ctx = canvas.getContext("2d");
    if (state.charts.category) {
      state.charts.category.destroy();
    }

    if (categories.length === 0) return;

    state.charts.category = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: dataCounts,
          backgroundColor: [
            "#6366f1",
            "#10b981",
            "#3b82f6",
            "#f59e0b",
            "#ec4899",
            "#8b5cf6"
          ],
          borderWidth: 2,
          borderColor: "#111827"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
            labels: { color: "#d1d5db", boxWidth: 14, font: { size: 11 } }
          }
        }
      }
    });
  } catch (err) {
    console.error("Category chart error:", err);
  }
}

// ==========================================
// REFLECTIONS & MOOD TAB
// ==========================================

async function loadTodayReflection() {
  const contentInput = document.getElementById("note-content");
  const moodValInput = document.getElementById("note-mood-val");
  if (!contentInput || !moodValInput) return;

  try {
    const res = await fetch(`${API_BASE}/notes?date=${state.selectedDate}`);
    if (res.ok && res.status !== 204) {
      const note = await res.json();
      if (note) {
        contentInput.value = note.content || "";
        const mood = note.mood || 5;
        moodValInput.value = mood;
        document.querySelectorAll(".mood-btn").forEach(btn => {
          btn.classList.toggle("active", btn.getAttribute("data-mood") === String(mood));
        });
        return;
      }
    }

    contentInput.value = "";
    moodValInput.value = 5;
    document.querySelectorAll(".mood-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-mood") === "5");
    });
  } catch (err) {
    console.error("Error loading daily note:", err);
  }
}

async function handleDailyNoteSubmit(e) {
  e.preventDefault();
  const mood = parseInt(document.getElementById("note-mood-val").value, 10);
  const content = document.getElementById("note-content").value.trim();

  try {
    const res = await fetch(`${API_BASE}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        note_date: state.selectedDate,
        mood: mood,
        content: content
      })
    });

    if (!res.ok) throw new Error("Gagal menyimpan refleksi harian");

    showToast("Catatan refleksi & mood berhasil disimpan!", "success");
    loadReflectionHistory();
  } catch (err) {
    showToast("Error: " + err.message, "error");
  }
}

async function loadReflectionHistory() {
  const container = document.getElementById("reflection-history-list");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/notes/history?limit=15`);
    if (!res.ok) return;
    const history = await res.json();

    const moodEmojiMap = {
      1: "😞",
      2: "🙁",
      3: "😐",
      4: "🙂",
      5: "🤩"
    };

    if (history.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-book-open"></i>
          <p>Belum ada riwayat catatan harian.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = history.map(h => {
      return `
        <div class="reflection-item">
          <div class="reflection-item-header">
            <span class="reflection-item-date">${formatDateIndo(h.note_date)}</span>
            <span class="reflection-item-mood">${moodEmojiMap[h.mood] || "🙂"}</span>
          </div>
          <div class="reflection-item-text">${escapeHtml(h.content || "Tidak ada catatan tertulis.")}</div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading reflection history:", err);
  }
}

// ==========================================
// HELPER SANITIZATION
// ==========================================

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeJs(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
}
