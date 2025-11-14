// app.js - 增強版

let allIncidents = [];
let allDefenses = {}; 
let incidentMapping = {}; 


async function loadData() {
  try {

    const [incidentsRes, defensesRes, mappingRes] = await Promise.all([
      fetch("incidents.json"),
      fetch("defenses.json"),
      fetch("mapping.json"),
    ]);

    const incidentsRaw = await incidentsRes.json();
    const defensesArray = await defensesRes.json();
    const mappingArray = await mappingRes.json();


    defensesArray.forEach((d) => {

      const idKey = (d.defense_id || "").trim();

      if (idKey) {
        
        allDefenses[idKey] = {
          id: idKey,
          name: d.name, // 讀取 'name'
          description: d.description, // 讀取 'description'
          tactic: d.tactic, // 讀取 'tactic'
        };
      }
    });

    
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

    
    allIncidents = incidentsRaw.map((incident) => {
      const id = incident.incident_id;
      return {
        ...incident,
       
        matched_defense_ids: incidentMapping[id] || [],
      };
    });


    allIncidents.sort((a, b) => a.incident_id - b.incident_id);

    renderIncidentList(allIncidents);
  } catch (error) {
    console.error("loading error:", error);
    document.getElementById("incident-list-container").innerHTML =
      "<p style='color:red;'>please make sure json files are in the right place。</p>";
  }
}


function renderIncidentList(incidentsToRender) {
  const listContainer = document.getElementById("incident-list");
  listContainer.innerHTML = ""; 

  if (incidentsToRender.length === 0) {
    listContainer.innerHTML = "<p>沒有找到符合條件的事故。</p>";
    return;
  }

  incidentsToRender.forEach((incident) => {
    const item = document.createElement("div");
    item.className = "incident-item";
 
    item.innerHTML = `<strong>ID ${incident.incident_id}:</strong> ${incident.incident_title}`;
    item.onclick = () => showIncidentDetail(incident);
    listContainer.appendChild(item);
  });


  if (
    incidentsToRender.length > 0 &&
    !document.getElementById("detail-title").textContent.includes("請選擇")
  ) {
    showIncidentDetail(incidentsToRender[0]);
  }
}


function handleSearch(event) {
  const query = event.target.value.toLowerCase();

  // mapping to mitre
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


function showIncidentDetail(incident) {
  const detailContainer = document.getElementById("incident-detail");


  document.getElementById(
    "detail-title"
  ).textContent = `ID ${incident.incident_id}: ${incident.incident_title}`;
  document.getElementById("detail-deployer").textContent =
    incident.deployer || "N/A";
  document.getElementById("detail-harmed").textContent =
    incident.harmed_parties || "N/A";
  document.getElementById("detail-mitre").textContent =
    incident.mitre_classification || "N/A";


  document.getElementById("detail-report").textContent =
    incident.full_report_text
      ? incident.full_report_text.slice(0, 1500) + "..."
      : "無詳細報告。";


  const defenseListContainer = document.getElementById("defense-match-list");
  defenseListContainer.innerHTML = "";

  const matchedIds = incident.matched_defense_ids || [];

  if (
    matchedIds.length === 0 ||
    matchedIds[0] === "JSON_PARSE_ERROR" ||
    matchedIds[0] === "LLM_ERROR"
  ) {
    defenseListContainer.innerHTML =
      '<p style="color: red;">LLM losting mapping result mapping.json。</p>';
    return;
  }

  defenseListContainer.innerHTML = "<h3>LLM recommended defense practices)</h3>";
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
      card.innerHTML = `<strong>${defenseId}:</strong> (Losting defense detail)`;
      defenseListContainer.appendChild(card);
    }
  });
}


function showDefenseModal(defense) {
  const modal = document.getElementById("defense-modal");

  document.getElementById("modal-title").textContent = defense.name;
  document.getElementById("modal-id").textContent = defense.id;
  document.getElementById("modal-tactic").textContent = defense.tactic || "N/A";
  document.getElementById("modal-description").textContent =
    defense.description;

  modal.style.display = "block";
}


function setupListeners() {

  document
    .getElementById("search-input")
    .addEventListener("input", handleSearch);


  document.querySelector(".close").onclick = function () {
    document.getElementById("defense-modal").style.display = "none";
  };
  window.onclick = function (event) {
    if (event.target == document.getElementById("defense-modal")) {
      document.getElementById("defense-modal").style.display = "none";
    }
  };
}


setupListeners();
loadData();
