let currentQueueId = null;
let editMode = false;

// state basis kasus
let bkPage = 1;
let bkSource = null;
let bkTotalPages = 1;
const BK_LIMIT = 50;

// =========================
// INISIALISASI AWAL
// =========================

document.addEventListener("DOMContentLoaded", function () {
  showRetrieve();
});

// =========================
// FORMAT ANGKA
// =========================

function formatRibuan(value) {
  const angka = value.replace(/\D/g, "");
  return angka.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function parseRibuan(value) {
  if (!value || value.trim() === "") return NaN;
  return parseInt(value.replace(/\./g, "")) || 0;
}

// =========================
// VALIDASI FORM
// =========================

const VALIDATION_RULES = {
  no_of_dependents: {
    label: "Jumlah Tanggungan",
    min: 0,
  },
  income_annum: {
    label: "Pendapatan Tahunan",
    min: 1,
  },
  loan_amount: {
    label: "Jumlah Pinjaman",
    min: 1,
  },
  loan_term: {
    label: "Tenor Pinjaman",
    min: 1,
  },
  cibil_score: {
    label: "Skor CIBIL",
    min: 300,
    max: 900,
  },
  residential_assets_value: {
    label: "Aset Rumah",
  },
  commercial_assets_value: {
    label: "Aset Komersial",
    min: 0,
  },
  luxury_assets_value: {
    label: "Aset Mewah",
    min: 0,
  },
  bank_asset_value: {
    label: "Aset Bank",
    min: 0,
  },
};

function showFieldError(fieldId, message) {
  const el = document.getElementById(fieldId);
  const errEl = document.getElementById(`err-${fieldId}`);
  if (el) el.classList.add("is-invalid");
  if (errEl) {
    errEl.textContent = "⚠ " + message;
    errEl.style.display = "block";
  }
}

function clearFieldError(fieldId) {
  const el = document.getElementById(fieldId);
  const errEl = document.getElementById(`err-${fieldId}`);
  if (el) el.classList.remove("is-invalid");
  if (errEl) {
    errEl.textContent = "";
    errEl.style.display = "none";
  }
}

function clearAllErrors() {
  Object.keys(VALIDATION_RULES).forEach((field) => clearFieldError(field));
}

function validateForm(data) {
  const errors = {};

  Object.entries(VALIDATION_RULES).forEach(([field, rules]) => {
    const value = data[field];

    // Cek kosong
    if (
      value === null ||
      value === undefined ||
      isNaN(value) ||
      (value === 0 && rules.min > 0)
    ) {
      errors[field] = `${rules.label} wajib diisi`;
      return;
    }

    // Cek batas bawah
    if (rules.min !== undefined && value < rules.min) {
      errors[field] =
        `${rules.label} tidak boleh kurang dari ${rules.min.toLocaleString("id-ID")}`;
      return;
    }

    // Cek batas atas
    if (rules.max !== undefined && value > rules.max) {
      errors[field] =
        `${rules.label} tidak boleh lebih dari ${rules.max.toLocaleString("id-ID")}`;
    }
  });

  return errors;
}

function formatRp(val) {
  return val != null ? Number(val).toLocaleString("id-ID") : "-";
}

function attachFormatListener() {
  document.querySelectorAll(".format-number").forEach((input) => {
    input.addEventListener("input", function () {
      const cursorPos = this.selectionStart;
      const prevLen = this.value.length;
      this.value = formatRibuan(this.value);
      const newLen = this.value.length;
      this.setSelectionRange(
        cursorPos + (newLen - prevLen),
        cursorPos + (newLen - prevLen),
      );
    });
  });
}

// =========================
// EVENT DELEGATION - ANALYZE
// =========================

document.addEventListener("click", async function (e) {
  if (e.target.id !== "analyzeBtn") return;

  e.preventDefault();
  e.stopPropagation();

  const data = {
    no_of_dependents: parseRibuan(
      document.getElementById("no_of_dependents").value,
    ),
    education: document.getElementById("education").value,
    self_employed: document.getElementById("self_employed").value,
    income_annum: parseRibuan(document.getElementById("income_annum").value),
    loan_amount: parseRibuan(document.getElementById("loan_amount").value),
    loan_term: parseRibuan(document.getElementById("loan_term").value),
    cibil_score: parseRibuan(document.getElementById("cibil_score").value),
    residential_assets_value: parseRibuan(
      document.getElementById("residential_assets_value").value,
    ),
    commercial_assets_value: parseRibuan(
      document.getElementById("commercial_assets_value").value,
    ),
    luxury_assets_value: parseRibuan(
      document.getElementById("luxury_assets_value").value,
    ),
    bank_asset_value: parseRibuan(
      document.getElementById("bank_asset_value").value,
    ),
  };

  // ── Validasi ──────────────────────────────
  clearAllErrors();
  const errors = validateForm(data);

  if (Object.keys(errors).length > 0) {
    Object.entries(errors).forEach(([field, msg]) =>
      showFieldError(field, msg),
    );
    window.scrollTo({ top: 0, behavior: "smooth" });
    return; // jangan kirim ke API
  }

  try {
    document.getElementById("result-area").innerHTML = `
      <div class="alert alert-info">Processing...</div>
    `;

    setFormDisabled(true);

    let url, method;
    if (editMode && currentQueueId) {
      url = `http://127.0.0.1:8000/revise/${currentQueueId}/edit`;
      method = "PUT";
    } else {
      url = "http://127.0.0.1:8000/cbr/retrieve-reuse";
      method = "POST";
    }

    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    console.log(JSON.stringify(result, null, 2));

    if (result.queue_id) {
      currentQueueId = result.queue_id;
    }

    if (editMode) {
      editMode = false;
      setFormDisabled(true);
      const editAlert = document.getElementById("edit-alert");
      if (editAlert) editAlert.remove();
    }

    const actionButtons = document.getElementById("action-buttons");
    if (actionButtons) actionButtons.classList.remove("d-none");

    let tableRows = "";
    result.top_cases.forEach(function (item) {
      tableRows += `
        <tr>
          <td>${item.rank}</td>
          <td>${item.loan_id}</td>
          <td>${item.decision}</td>
          <td>${item.similarity}</td>
        </tr>
      `;
    });

    document.getElementById("result-area").innerHTML = `
      <div class="card shadow-sm p-4 mb-4">
        <h3 class="text-success mb-3">Top Recommendation</h3>
        <p><strong>Decision:</strong> ${result.reuse.recommendation}</p>
        <p><strong>Similarity Score:</strong> ${result.reuse.similarity_score}</p>
        <p><strong>Confidence:</strong> ${result.reuse.confidence}</p>
        <p><strong>Majority Vote:</strong> ${result.reuse.majority_vote}</p>
        <p><strong>Note:</strong> ${result.reuse.note}</p>
      </div>
      <div class="card shadow-sm p-4">
        <h4 class="mb-3">Top 5 Similar Cases</h4>
        <div class="table-responsive">
          <table class="table table-bordered">
            <thead class="table-dark">
              <tr>
                <th>Rank</th>
                <th>Loan ID</th>
                <th>Decision</th>
                <th>Similarity</th>
              </tr>
            </thead>
            <tbody>${tableRows}</tbody>
          </table>
        </div>
      </div>
    `;
  } catch (error) {
    console.error(error);
    setFormDisabled(false);
    document.getElementById("result-area").innerHTML = `
      <div class="alert alert-danger">Failed connect to API</div>
    `;
  }
});

// =========================
// SHOW RETRIEVE
// =========================

async function showRetrieve() {
  setActiveMenu("menu-retrieve");
  const container = document.getElementById("main-content");
  try {
    const response = await fetch("pages/retrieve.html");
    const html = await response.text();
    container.innerHTML = html;
    attachFormatListener();
    document
      .getElementById("btn-edit")
      ?.addEventListener("click", enableEditMode);
    document
      .getElementById("btn-new")
      ?.addEventListener("click", resetRetrieveForm);
    document
      .getElementById("btn-revise")
      ?.addEventListener("click", showRevise);
    currentQueueId = null;
    editMode = false;
  } catch (error) {
    console.error("Gagal load retrieve.html:", error);
    container.innerHTML = `<div class="alert alert-danger">Gagal memuat halaman Retrieve.</div>`;
  }
}

// =========================
// SHOW REVISE
// =========================

async function showRevise() {
  setActiveMenu("menu-revise");
  const container = document.getElementById("main-content");
  try {
    const response = await fetch("pages/revise.html");
    const html = await response.text();
    container.innerHTML = html;
    await loadPendingRevise();
  } catch (error) {
    console.error("Gagal load revise.html:", error);
    container.innerHTML = `<div class="alert alert-danger">Gagal memuat halaman Revise.</div>`;
  }
}

async function loadPendingRevise() {
  try {
    const response = await fetch("http://127.0.0.1:8000/revise/pending");
    const result = await response.json();

    if (result.total === 0) {
      document.getElementById("revise-list").innerHTML = `
        <div class="alert alert-warning">No revise queue available</div>
      `;
      return;
    }

    let html = "";
    result.items.forEach(function (item) {
      const rec = item.recommendation ?? item.top_cases[0].decision;
      const recColor = rec === "Approved" ? "text-success" : "text-danger";

      html += `
        <div class="card mb-3 shadow-sm" 
             style="cursor:pointer; transition: box-shadow 0.2s;"
             onmouseover="this.style.boxShadow='0 4px 15px rgba(0,0,0,0.15)'"
             onmouseout="this.style.boxShadow=''"
             onclick="showReviseDetail(${item.id})">
          <div class="card-body d-flex justify-content-between align-items-center">
            <div>
              <h6 class="mb-1 fw-bold">Queue ID: ${item.id}</h6>
              <span class="text-muted small">Klik untuk lihat detail & buat keputusan</span>
            </div>
            <div class="text-end">
              <div class="fw-bold ${recColor}">${rec}</div>
              <small class="text-muted">Rekomendasi Sistem</small>
            </div>
          </div>
        </div>
      `;
    });

    document.getElementById("revise-list").innerHTML = html;
  } catch (error) {
    console.error(error);
    document.getElementById("revise-list").innerHTML = `
      <div class="alert alert-danger">Failed load revise queue</div>
    `;
  }
}

// =========================
// SHOW REVISE DETAIL
// =========================

async function showReviseDetail(queueId) {
  const container = document.getElementById("main-content");

  try {
    // load template halaman detail
    const pageRes = await fetch("pages/revise-detail.html");
    const html = await pageRes.text();
    container.innerHTML = html;

    // set queue id di judul
    document.getElementById("detail-queue-id").textContent =
      `Queue ID: ${queueId}`;

    // simpan queue id aktif
    currentQueueId = queueId;

    // fetch data queue dari backend
    const dataRes = await fetch(`http://127.0.0.1:8000/revise/pending`);
    const result = await dataRes.json();

    // cari item yang sesuai
    const item = result.items.find((i) => i.id === queueId);
    if (!item) {
      container.innerHTML = `<div class="alert alert-danger">Data queue tidak ditemukan.</div>`;
      return;
    }

    // render data input pemohon
    const input = item.input_case;
    const inputRows = [
      ["Jumlah Tanggungan", input.no_of_dependents],
      ["Pendidikan", input.education],
      ["Status Wiraswasta", input.self_employed],
      ["Pendapatan Tahunan", formatRp(input.income_annum)],
      ["Jumlah Pinjaman", formatRp(input.loan_amount)],
      ["Tenor Pinjaman", `${input.loan_term} bulan`],
      ["CIBIL Score", input.cibil_score],
      ["Aset Rumah", formatRp(input.residential_assets_value)],
      ["Aset Komersial", formatRp(input.commercial_assets_value)],
      ["Aset Mewah", formatRp(input.luxury_assets_value)],
      ["Aset Bank", formatRp(input.bank_asset_value)],
    ];

    document.getElementById("detail-input-data").innerHTML = inputRows
      .map(
        ([label, val]) => `
      <tr>
        <td class="text-muted" style="width:55%">${label}</td>
        <td class="fw-semibold">${val}</td>
      </tr>
    `,
      )
      .join("");

    // render rekomendasi sistem
    const rec = item.recommendation ?? item.top_cases[0].decision;
    const recColor = rec === "Approved" ? "success" : "danger";

    document.getElementById("detail-recommendation").innerHTML = `
      <div class="d-flex align-items-center mb-3">
        <span class="badge bg-${recColor} fs-6 me-2">${rec}</span>
        <span class="text-muted small">Rekomendasi Utama</span>
      </div>
      <table class="table table-sm table-borderless">
        <tbody>
          <tr>
            <td class="text-muted" style="width:50%">Similarity Score</td>
            <td class="fw-semibold">${item.similarity_score ?? "-"}</td>
          </tr>
          <tr>
            <td class="text-muted">Confidence</td>
            <td class="fw-semibold">${item.confidence ?? "-"}</td>
          </tr>
          <tr>
            <td class="text-muted">Majority Vote</td>
            <td class="fw-semibold">${item.majority_vote ?? "-"}</td>
          </tr>
          <tr>
            <td class="text-muted">Catatan Sistem</td>
            <td class="fw-semibold">${item.note ?? "-"}</td>
          </tr>
        </tbody>
      </table>
    `;

    // set default dropdown sesuai rekomendasi
    document.getElementById("detail-decision").value = rec;

    // render top 5 kasus serupa
    let topRows = "";
    item.top_cases.forEach(function (tc) {
      const color = tc.decision === "Approved" ? "text-success" : "text-danger";
      topRows += `
        <tr>
          <td>${tc.rank}</td>
          <td>${tc.loan_id}</td>
          <td class="${color} fw-bold">${tc.decision}</td>
          <td>${tc.similarity}</td>
        </tr>
      `;
    });
    document.getElementById("detail-top-cases").innerHTML = topRows;
  } catch (error) {
    console.error(error);
    container.innerHTML = `<div class="alert alert-danger">Gagal memuat detail queue.</div>`;
  }
}

// =========================
// SAVE REVISE DARI DETAIL
// =========================

async function saveReviseFromDetail() {
  if (!currentQueueId) {
    alert("Queue ID tidak ditemukan");
    return;
  }

  const decision = document.getElementById("detail-decision").value;
  const btn = document.getElementById("detail-save-btn");

  btn.disabled = true;
  btn.textContent = "Menyimpan...";

  try {
    const response = await fetch(
      `http://127.0.0.1:8000/revise/${currentQueueId}/save`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expert_decision: decision }),
      },
    );

    const result = await response.json();
    console.log(JSON.stringify(result, null, 2));

    alert(`Keputusan "${decision}" berhasil disimpan!`);
    currentQueueId = null;
    showRevise(); // kembali ke daftar queue
  } catch (error) {
    console.error(error);
    alert("Gagal menyimpan keputusan");
    btn.disabled = false;
    btn.textContent = "Simpan Keputusan";
  }
}

// =========================
// SHOW HISTORY
// =========================

async function showHistory() {
  setActiveMenu("menu-history");
  const container = document.getElementById("main-content");
  try {
    const response = await fetch("pages/history.html");
    const html = await response.text();
    container.innerHTML = html;
    await loadHistory();
  } catch (error) {
    console.error("Gagal load history:", error);
    container.innerHTML = `<div class="alert alert-danger">Gagal memuat halaman History.</div>`;
  }
}

async function loadHistory() {
  try {
    const response = await fetch("http://127.0.0.1:8000/revise/history");
    const result = await response.json();

    if (result.total === 0) {
      document.getElementById("history-area").innerHTML = `
        <div class="alert alert-warning">History masih kosong</div>
      `;
      return;
    }

    let rows = "";
    result.items.forEach(function (item) {
      rows += `
        <tr>
          <td>${item.id}</td>
          <td>${item.loan_id}</td>
          <td>${item.recommendation}</td>
          <td>${item.expert_decision}</td>
          <td>${item.status}</td>
          <td>${item.revised_at}</td>
        </tr>
      `;
    });

    document.getElementById("history-area").innerHTML = `
      <div class="card shadow-sm p-4">
        <h4 class="mb-3">Total: ${result.total} history</h4>
        <div class="table-responsive">
          <table class="table table-bordered table-striped text-center">
            <thead class="table-dark">
              <tr>
                <th>ID</th>
                <th>Loan ID</th>
                <th>Recommendation</th>
                <th>Expert Decision</th>
                <th>Status</th>
                <th>Revised At</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  } catch (error) {
    console.error(error);
    document.getElementById("history-area").innerHTML = `
      <div class="alert alert-danger">Failed load history</div>
    `;
  }
}

// =========================
// SHOW BASIS KASUS
// =========================

async function showBasisKasus() {
  setActiveMenu("menu-basis-kasus");
  const container = document.getElementById("main-content");
  try {
    const response = await fetch("pages/basis-kasus.html");
    const html = await response.text();
    container.innerHTML = html;
    bkPage = 1;
    bkSource = null;
    bkTotalPages = 1;
    await loadBasisKasus();
  } catch (error) {
    console.error("Gagal load basis-kasus.html:", error);
    container.innerHTML = `<div class="alert alert-danger">Gagal memuat halaman Basis Kasus.</div>`;
  }
}

async function loadBasisKasus() {
  try {
    let url = `http://127.0.0.1:8000/cbr/cases?page=${bkPage}&limit=${BK_LIMIT}`;
    if (bkSource) url += `&source=${bkSource}`;

    const response = await fetch(url);
    const result = await response.json();

    bkTotalPages = result.total_pages;

    document.getElementById("bk-total-info").textContent =
      `Total: ${result.total.toLocaleString("id-ID")} kasus`;
    document.getElementById("bk-page-info").textContent =
      `Halaman ${bkPage} dari ${bkTotalPages}`;

    document.getElementById("btn-prev").disabled = bkPage <= 1;
    document.getElementById("btn-next").disabled = bkPage >= bkTotalPages;
    document.getElementById("btn-last").disabled = bkPage >= bkTotalPages;

    let rows = "";
    result.items.forEach(function (item) {
      const isRetained = item.source === "retained";
      const rowStyle = isRetained ? 'style="background-color: #ecfdf5;"' : "";
      const statusColor =
        item.loan_status === "Approved" ? "text-success" : "text-danger";
      const sourceBadge = isRetained
        ? `<span class="badge bg-success">retained</span>`
        : `<span class="badge bg-secondary">initial</span>`;

      rows += `
        <tr ${rowStyle}>
          <td>${item.loan_id}</td>
          <td>${item.no_of_dependents}</td>
          <td>${item.education}</td>
          <td>${item.self_employed}</td>
          <td>${formatRp(item.income_annum)}</td>
          <td>${formatRp(item.loan_amount)}</td>
          <td>${item.loan_term}</td>
          <td>${item.cibil_score}</td>
          <td>${formatRp(item.residential_assets_value)}</td>
          <td>${formatRp(item.commercial_assets_value)}</td>
          <td>${formatRp(item.luxury_assets_value)}</td>
          <td>${formatRp(item.bank_asset_value)}</td>
          <td class="${statusColor} fw-bold">${item.loan_status}</td>
        </tr>
      `;
    });

    document.getElementById("bk-table-body").innerHTML =
      rows ||
      `
      <tr><td colspan="10" class="text-center">Tidak ada data</td></tr>
    `;
  } catch (error) {
    console.error(error);
    document.getElementById("bk-table-body").innerHTML = `
      <tr><td colspan="10" class="text-center text-danger">Gagal memuat data</td></tr>
    `;
  }
}

function filterBasisKasus(source) {
  bkSource = source;
  bkPage = 1;

  document.getElementById("filter-all").className =
    "btn btn-sm " + (source === null ? "btn-primary" : "btn-outline-secondary");
  document.getElementById("filter-initial").className =
    "btn btn-sm " +
    (source === "initial" ? "btn-secondary" : "btn-outline-secondary");
  document.getElementById("filter-retained").className =
    "btn btn-sm " +
    (source === "retained" ? "btn-success" : "btn-outline-success");

  loadBasisKasus();
}

function changePage(delta) {
  const newPage = bkPage + delta;
  if (newPage < 1 || newPage > bkTotalPages) return;
  bkPage = newPage;
  loadBasisKasus();
}

function goToLastPage() {
  bkPage = bkTotalPages;
  loadBasisKasus();
}

// =========================
// HELPER FUNCTIONS
// =========================

function setActiveMenu(menuId) {
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });
  document.getElementById(menuId).classList.add("active");
}

function setFormDisabled(disabled) {
  const ids = [
    "no_of_dependents",
    "education",
    "self_employed",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
  ];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.disabled = disabled;
  });
}

function resetRetrieveForm() {
  const ids = [
    "no_of_dependents",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
  ];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });

  document.getElementById("education").value = "Graduate";
  document.getElementById("self_employed").value = "Yes";
  document.getElementById("result-area").innerHTML = "";
  document.getElementById("action-buttons").classList.add("d-none");

  const editAlert = document.getElementById("edit-alert");
  if (editAlert) editAlert.remove();

  setFormDisabled(false);
  currentQueueId = null;
  editMode = false;
  clearAllErrors();
}

function enableEditMode() {
  if (!currentQueueId) {
    alert("Queue ID tidak ditemukan");
    return;
  }
  editMode = true;
  setFormDisabled(false);
  const oldAlert = document.getElementById("edit-alert");
  if (!oldAlert) {
    document.getElementById("result-area").insertAdjacentHTML(
      "afterbegin",
      `<div id="edit-alert" class="alert alert-warning">
        Anda sedang mengedit kasus Queue ID: <b>${currentQueueId}</b>
      </div>`,
    );
  }
}

async function showEvaluation() {
  setActiveMenu("menu-evaluation");
  const mainContent = document.getElementById("main-content");

  mainContent.innerHTML = `
        <h2>Evaluasi Sistem CBR</h2>

        <div id="evaluation-content">
            <p>Memuat data evaluasi...</p>
        </div>
    `;

  try {
    const response = await fetch("http://localhost:8000/evaluation/results");

    const data = await response.json();

    if (data.status === "not_started") {
      document.getElementById("evaluation-content").innerHTML = `
                <div class="alert alert-warning">
                    Hasil evaluasi belum tersedia.
                </div>
            `;

      return;
    }

    document.getElementById("evaluation-content").innerHTML = `
            <div class="row mb-4">

                <div class="col-md-3 d-flex">
                    <div class="card text-center w-120">
                        <div class="card-body d-flex flex-column justify-content-center">
                            <h5>Accuracy</h5>
                            <h3>${data.accuracy}%</h3>
                            <small class="text-muted">Persentase prediksi yang benar dari seluruh data uji</small>
                        </div>
                    </div>
                </div>

                <div class="col-md-3 d-flex">
                    <div class="card text-center w-120">
                        <div class="card-body d-flex flex-column justify-content-center">
                            <h5>Precision</h5>
                            <h3>${data.precision}%</h3>
                            <small class="text-muted">Persentase ketepatan sistem saat memberikan prediksi positif (Approved)</small>
                        </div>
                    </div>
                </div>

                <div class="col-md-3 d-flex">
                    <div class="card text-center w-120">
                        <div class="card-body d-flex flex-column justify-content-center">
                            <h5>Recall</h5>
                            <h3>${data.recall}%</h3>
                            <small class="text-muted">Persentase kemampuan sistem menemukan seluruh pinjaman yang layak disetujui</small>
                        </div>
                    </div>
                </div>

                <div class="col-md-3 d-flex">
                    <div class="card text-center w-120">
                        <div class="card-body d-flex flex-column justify-content-center">
                            <h5>F1-Score</h5>
                            <h3>${data.f1_score}%</h3>
                            <small class="text-muted">Keseimbangan antara Precision dan Recall, memberikan gambaran keseluruhan kinerja sistem</small>
                        </div>
                    </div>
                </div>

            </div>

            <h4>Informasi Dataset</h4>

            <ul>
                <li>Data Training : ${data.train_size}</li>
                <li>Data Testing : ${data.test_size}</li>
                <li>Top-N : ${data.top_n}</li>
            </ul>

            <h4>Confusion Matrix</h4>

            <table class="table table-bordered text-center">

                <thead>
                    <tr>
                        <th>Kondisi Sebenarnya</th>
                        <th>Prediksi Approved</th>
                        <th>Prediksi Rejected</th>
                    </tr>
                </thead>

                <tbody>
                    <tr>
                        <th>Approved</th>
                        <td>${data.confusion_matrix.tp}</td>
                        <td>${data.confusion_matrix.fn}</td>
                    </tr>

                    <tr>
                        <th>Rejected</th>
                        <td>${data.confusion_matrix.fp}</td>
                        <td>${data.confusion_matrix.tn}</td>
                    </tr>
                </tbody>

            </table>
        `;
  } catch (err) {
    console.error(err);

    document.getElementById("evaluation-content").innerHTML = `
            <div class="alert alert-danger">
                Gagal mengambil data evaluasi.
            </div>
        `;
  }
}
