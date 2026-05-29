document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // RETRIEVE & REUSE
    // =========================

    const button = document.getElementById("analyzeBtn");

    if(button){

        button.addEventListener("click", async function () {

            // ambil input form
            const data = {

                no_of_dependents: parseInt(
                    document.getElementById("no_of_dependents").value
                ),

                education:
                    document.getElementById("education").value,

                self_employed:
                    document.getElementById("self_employed").value,

                income_annum: parseInt(
                    document.getElementById("income_annum").value
                ),

                loan_amount: parseInt(
                    document.getElementById("loan_amount").value
                ),

                loan_term: parseInt(
                    document.getElementById("loan_term").value
                ),

                cibil_score: parseInt(
                    document.getElementById("cibil_score").value
                ),

                residential_assets_value: parseInt(
                    document.getElementById("residential_assets_value").value
                ),

                commercial_assets_value: parseInt(
                    document.getElementById("commercial_assets_value").value
                ),

                luxury_assets_value: parseInt(
                    document.getElementById("luxury_assets_value").value
                ),

                bank_asset_value: parseInt(
                    document.getElementById("bank_asset_value").value
                )

            };

            try {

                // loading
                document.getElementById("result-area").innerHTML = `

                    <div class="alert alert-info">
                        Processing...
                    </div>

                `;

                // request API
                const response = await fetch(
                    "http://127.0.0.1:8000/cbr/retrieve-reuse",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify(data)
                    }
                );

                const result = await response.json();

                console.log(result);

                // top 5 rows
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

                // tampil hasil
                document.getElementById("result-area").innerHTML = `

                    <!-- TOP RECOMMENDATION -->
                    <div class="card shadow-sm p-4 mb-4">

                        <h3 class="text-success mb-3">
                            Top Recommendation
                        </h3>

                        <p>
                            <strong>Decision:</strong>
                            ${result.reuse.recommendation}
                        </p>

                        <p>
                            <strong>Similarity Score:</strong>
                            ${result.reuse.similarity_score}
                        </p>

                        <p>
                            <strong>Confidence:</strong>
                            ${result.reuse.confidence}
                        </p>

                        <p>
                            <strong>Majority Vote:</strong>
                            ${result.reuse.majority_vote}
                        </p>

                        <p>
                            <strong>Note:</strong>
                            ${result.reuse.note}
                        </p>

                    </div>

                    <!-- TOP 5 -->
                    <div class="card shadow-sm p-4">

                        <h4 class="mb-3">
                            Top 5 Similar Cases
                        </h4>

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

                                <tbody>

                                    ${tableRows}

                                </tbody>

                            </table>

                        </div>

                    </div>

                `;

            } catch (error) {

                console.error(error);

                document.getElementById("result-area").innerHTML = `

                    <div class="alert alert-danger">
                        Failed connect to API
                    </div>

                `;

            }

        });

    }

});


// =========================
// SHOW RETRIEVE
// =========================

function showRetrieve(){

    document.querySelectorAll(".nav-link")
        .forEach(link => {
            link.classList.remove("active");
        });

    document.getElementById("menu-retrieve")
        .classList.add("active");

    location.reload();

}


// =========================
// SHOW REVISE
// =========================

async function showRevise(){

    // active menu
    document.querySelectorAll(".nav-link")
        .forEach(link => {
            link.classList.remove("active");
        });

    document.getElementById("menu-revise")
        .classList.add("active");

    const container = document.getElementById("main-content");

    container.innerHTML = `

        <h2 class="mb-4">
            Revise Queue
        </h2>

        <div id="revise-list">

            <div class="alert alert-info">
                Loading revise queue...
            </div>

        </div>

    `;

    try{

        const response = await fetch(
            "http://127.0.0.1:8000/revise/pending"
        );

        const result = await response.json();

        console.log(result);

        // jika kosong
        if(result.total === 0){

            document.getElementById("revise-list").innerHTML = `

                <div class="alert alert-warning">
                    No revise queue available
                </div>

            `;

            return;

        }

        let html = "";

        result.items.forEach(function(item){

            html += `

                <div class="card p-4 mb-3 shadow-sm">

                    <h5>
                        Queue ID: ${item.id}
                    </h5>

                    <p>
                        Recommendation:
                        <b>${item.top_cases[0].decision}</b>
                    </p>

                    <select
                        class="form-select mb-3"
                        id="decision-${item.id}">

                        <option value="Approved">
                            Approved
                        </option>

                        <option value="Rejected">
                            Rejected
                        </option>

                    </select>

                    <button
                        class="btn btn-success"
                        onclick="saveRevise(${item.id})">

                        Save Revision

                    </button>

                </div>

            `;

        });

        document.getElementById("revise-list").innerHTML = html;

    }catch(error){

        console.error(error);

        document.getElementById("revise-list").innerHTML = `

            <div class="alert alert-danger">
                Failed load revise queue
            </div>

        `;

    }

}


// =========================
// SAVE REVISE
// =========================

async function saveRevise(queueId){

    const decision = document.getElementById(
        `decision-${queueId}`
    ).value;

    try{

        const response = await fetch(
            `http://127.0.0.1:8000/revise/${queueId}/save`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    expert_decision: decision
                })
            }
        );

        const result = await response.json();

        console.log(result);

        alert("Revision saved successfully");

        // reload queue
        showRevise();

    }catch(error){

        console.error(error);

        alert("Failed save revise");

    }

}


// =========================
// SHOW DATABASE
// =========================

async function showDatabase() {

    // active menu
    document.querySelectorAll(".nav-link")
        .forEach(link => {
            link.classList.remove("active");
        });

    document.getElementById("menu-database")
        .classList.add("active");

    const container = document.getElementById("main-content");

    // loading
    container.innerHTML = `

        <h2 class="mb-4">
            Database
        </h2>

        <div id="database-area">

            <div class="alert alert-info">
                Loading database...
            </div>

        </div>

    `;

    try {

        // ambil data revise history
        const response = await fetch(
            "http://127.0.0.1:8000/revise/history"
        );

        const result = await response.json();

        console.log(result);

        // jika kosong
        if(result.total === 0){

            document.getElementById("database-area").innerHTML = `

                <div class="alert alert-warning">
                    Database masih kosong
                </div>

            `;

            return;
        }

        let rows = "";

        result.items.forEach(function(item){

            rows += `

                <tr>

                    <td>${item.id}</td>

                    <td>
                        ${item.input_case.income_annum}
                    </td>

                    <td>
                        ${item.input_case.loan_amount}
                    </td>

                    <td>
                        ${item.recommendation}
                    </td>

                    <td>
                        ${item.expert_decision}
                    </td>

                    <td>
                        ${item.status}
                    </td>

                    <td>
                        ${item.revised_at}
                    </td>

                </tr>

            `;

        });

        document.getElementById("database-area").innerHTML = `

            <div class="card shadow-sm p-4">

                <h4 class="mb-3">
                    Total Data: ${result.total}
                </h4>

                <div class="table-responsive">

                    <table class="table table-bordered table-striped">

                        <thead class="table-dark">

                            <tr>

                                <th>ID</th>
                                <th>Income</th>
                                <th>Loan Amount</th>
                                <th>Recommendation</th>
                                <th>Expert Decision</th>
                                <th>Status</th>
                                <th>Revised At</th>

                            </tr>

                        </thead>

                        <tbody>

                            ${rows}

                        </tbody>

                    </table>

                </div>

            </div>

        `;

    } catch(error) {

        console.error(error);

        document.getElementById("database-area").innerHTML = `

            <div class="alert alert-danger">
                Failed load database
            </div>

        `;

    }

}