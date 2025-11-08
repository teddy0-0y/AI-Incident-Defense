// app.js - 增強版

// 核心數據結構
let allIncidents = []; // 原始事故列表
let allDefenses = {}; // 防禦清單 (Key: ID)
let incidentMapping = {}; // 配對結果 (Key: Incident ID)

// --- 數據加載 ---
async function loadData() {
  try {
    // 確保檔案名稱與您 Python 轉換後的 JSON 檔案一致
    const [incidentsRes, defensesRes, mappingRes] = await Promise.all([
      fetch("incidents.json"),
      fetch("defenses.json"),
      fetch("mapping.json"),
    ]);

    const incidentsRaw = await incidentsRes.json();
    const defensesArray = await defensesRes.json();
    const mappingArray = await mappingRes.json();

    // 1. 轉換防禦清單為字典 (Key: ID)
    defensesArray.forEach((d) => {
      // *** 這是關鍵修正 ***
      // 您的 JSON 檔案使用的是 "defense_id"，不是 "Technique ID"
      // 我們同時使用 .trim() 來清除 LLM 可能產生的隱藏空格
      const idKey = (d.defense_id || "").trim();

      if (idKey) {
        // 確保 idKey 不是空的
        allDefenses[idKey] = {
          id: idKey,
          name: d.name, // 讀取 'name'
          description: d.description, // 讀取 'description'
          tactic: d.tactic, // 讀取 'tactic'
        };
      }
    });

    // 2. 轉換配對結果 (您的代碼是正確的，我們只增加 .trim() 來增加穩定性)
    mappingArray.forEach((m) => {
      let ids = m.matched_defense_ids;
      if (typeof ids === "string") {
        ids = ids
          .split(",")
          .map((id) => (id || "").trim()) // 增加 (id || '') 和 .trim() 清潔
          .filter((id) => id.length > 0);
      }
      incidentMapping[m.incident_id] = ids;
    });

    // 3. 整合所有數據到 incidents 列表中 (您的代碼是正確的)
    allIncidents = incidentsRaw.map((incident) => {
      const id = incident.incident_id;
      return {
        ...incident,
        // 加入配對的防禦 ID 列表，如果沒有配對則為空數組
        matched_defense_ids: incidentMapping[id] || [],
      };
    });

    // 按照 ID 排序 (您的代碼是正確的)
    allIncidents.sort((a, b) => a.incident_id - b.incident_id);

    renderIncidentList(allIncidents);
  } catch (error) {
    console.error("加載數據失敗:", error);
    document.getElementById("incident-list-container").innerHTML =
      "<p style='color:red;'>錯誤：無法加載數據檔案。請確保三個 JSON 文件存在。</p>";
  }
}

// --- 渲染事件列表 ---
function renderIncidentList(incidentsToRender) {
  const listContainer = document.getElementById("incident-list");
  listContainer.innerHTML = ""; // 清空列表

  if (incidentsToRender.length === 0) {
    listContainer.innerHTML = "<p>沒有找到符合條件的事故。</p>";
    return;
  }

  incidentsToRender.forEach((incident) => {
    const item = document.createElement("div");
    item.className = "incident-item";
    // 顯示 ID 和標題
    item.innerHTML = `<strong>ID ${incident.incident_id}:</strong> ${incident.incident_title}`;
    item.onclick = () => showIncidentDetail(incident);
    listContainer.appendChild(item);
  });

  // 預設顯示列表中的第一個事件
  if (
    incidentsToRender.length > 0 &&
    !document.getElementById("detail-title").textContent.includes("請選擇")
  ) {
    showIncidentDetail(incidentsToRender[0]);
  }
}

// --- 搜尋邏輯 ---
function handleSearch(event) {
  const query = event.target.value.toLowerCase();

  // 過濾邏輯：匹配標題、報告文本或 MITRE 分類
  const filteredIncidents = allIncidents.filter((incident) => {
    const titleMatch =
      incident.incident_title &&
      incident.incident_title.toLowerCase().includes(query);
    const reportMatch =
      incident.full_report_text &&
      incident.full_report_text.toLowerCase().includes(query);
    const mitreMatch =
      incident.mitre_classification &&
      incident.mitre_classification.toLowerCase().includes(query);

    return titleMatch || reportMatch || mitreMatch;
  });

  renderIncidentList(filteredIncidents);
}

// --- 渲染事件詳細資訊 ---
function showIncidentDetail(incident) {
  const detailContainer = document.getElementById("incident-detail");

  // 更新事件概況資訊
  document.getElementById(
    "detail-title"
  ).textContent = `ID ${incident.incident_id}: ${incident.incident_title}`;
  document.getElementById("detail-deployer").textContent =
    incident.deployer || "N/A";
  document.getElementById("detail-harmed").textContent =
    incident.harmed_parties || "N/A";
  document.getElementById("detail-mitre").textContent =
    incident.mitre_classification || "N/A";

  // 顯示詳細報告 (截斷長度，避免過長)
  document.getElementById("detail-report").textContent =
    incident.full_report_text
      ? incident.full_report_text.slice(0, 1500) + "..."
      : "無詳細報告。";

  // 渲染 LLM 配對的防禦手法
  const defenseListContainer = document.getElementById("defense-match-list");
  defenseListContainer.innerHTML = "";

  const matchedIds = incident.matched_defense_ids || [];

  if (
    matchedIds.length === 0 ||
    matchedIds[0] === "JSON_PARSE_ERROR" ||
    matchedIds[0] === "LLM_ERROR"
  ) {
    defenseListContainer.innerHTML =
      '<p style="color: red;">LLM 配對結果失敗或缺失。請檢查 mapping.json。</p>';
    return;
  }

  defenseListContainer.innerHTML = "<h3>LLM 建議的防禦手法 (點擊查看詳情)</h3>";
  matchedIds.forEach((defenseId) => {
    const defense = allDefenses[defenseId];
    if (defense) {
      const card = document.createElement("div");
      card.className = "defense-card";
      card.innerHTML = `<strong>${defense.id}:</strong> ${defense.name}`;
      card.onclick = () => showDefenseModal(defense);
      defenseListContainer.appendChild(card);
    } else {
      const card = document.createElement("div");
      card.className = "defense-card";
      card.innerHTML = `<strong>${defenseId}:</strong> (防禦細節缺失)`;
      defenseListContainer.appendChild(card);
    }
  });
}

// --- 渲染防禦手法彈窗 ---
function showDefenseModal(defense) {
  const modal = document.getElementById("defense-modal");

  document.getElementById("modal-title").textContent = defense.name;
  document.getElementById("modal-id").textContent = defense.id;
  document.getElementById("modal-tactic").textContent = defense.tactic || "N/A";
  document.getElementById("modal-description").textContent =
    defense.description;

  modal.style.display = "block";
}

// --- 設置事件監聽器和啟動 ---
function setupListeners() {
  // 搜尋框的事件監聽器
  document
    .getElementById("search-input")
    .addEventListener("input", handleSearch);

  // Modal 關閉邏輯
  document.querySelector(".close").onclick = function () {
    document.getElementById("defense-modal").style.display = "none";
  };
  window.onclick = function (event) {
    if (event.target == document.getElementById("defense-modal")) {
      document.getElementById("defense-modal").style.display = "none";
    }
  };
}

// 啟動應用程式
setupListeners();
loadData();
