class BattleProfileRenderer {
    constructor() {
        this.data = null;
    }

    async loadData() {
        try {
            const response = await fetch('data/battleprofile.json');
            this.data = await response.json();
            return this.data;
        } catch (error) {
            console.error('Error loading battle profile data:', error);
            return null;
        }
    }

    renderUniversalManifestations() {
        if (!this.data || !this.data.data || !this.data.data.universal_manifestations) {
            return '<p>No Universal Manifestations data available.</p>';
        }

        const manifestations = this.data.data.universal_manifestations;

        // Sort manifestations by points (descending) then by name (alphabetically)
        const sortedManifestations = manifestations.sort((a, b) => {
            const pointsA = a.points !== undefined ? a.points : 0;
            const pointsB = b.points !== undefined ? b.points : 0;

            if (pointsA !== pointsB) {
                return pointsB - pointsA; // Sort by points descending (highest first)
            }

            // If points are equal, sort alphabetically by name
            const nameA = (a.name || '').toLowerCase();
            const nameB = (b.name || '').toLowerCase();
            return nameA.localeCompare(nameB);
        });

        let html = `
            <div class="table-container">
                <table class="bp-table two-column-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Points</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        sortedManifestations.forEach((manifestation, index) => {
            const rowClass = index % 2 === 0 ? 'even-row' : 'odd-row';
            html += `
                        <tr class="${rowClass}">
                            <td>${manifestation.name}</td>
                            <td>${manifestation.points}</td>
                        </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    renderArmies() {
        if (!this.data || !this.data.data || !this.data.data.factions) {
            return '<p>No Army data available.</p>';
        }

        const factions = this.data.data.factions;

        let html = `
            <div class="army-selector-container">
                <label for="army-select">Select Army:</label>
                <select id="army-select" onchange="renderSelectedArmy()">
                    <option value="">-- Choose an Army --</option>
        `;

        // Add faction options
        factions.forEach(faction => {
            html += `<option value="${faction.name}">${faction.name}</option>`;
        });

        html += `
                </select>
            </div>
            <div id="army-content">
                <p>Please select an army from the dropdown above.</p>
            </div>
        `;

        return html;
    }

    renderSelectedArmyContent(armyName) {
        if (!this.data || !this.data.data || !this.data.data.factions) {
            return '<p>No Army data available.</p>';
        }

        const faction = this.data.data.factions.find(f => f.name === armyName);
        if (!faction) {
            return '<p>Army not found.</p>';
        }

        let html = `<h3>${armyName}</h3>`;

        // Process battle profiles and separate heroes from units
        if (faction.battle_profiles && faction.battle_profiles.length > 0) {
            const heroes = faction.battle_profiles.filter(profile => profile.hero === true);
            const units = faction.battle_profiles.filter(profile => profile.hero !== true);

            // Render Heroes table
            if (heroes.length > 0) {
                html += this.renderHeroesTable(heroes);
            } else {
                html += this.renderEmptyHeroesTable();
            }

            // Render Units table  
            if (units.length > 0) {
                html += this.renderUnitsTable(units);
            } else {
                html += this.renderEmptyUnitsTable();
            }
        } else {
            // Render empty placeholder tables
            html += this.renderEmptyHeroesTable();
            html += this.renderEmptyUnitsTable();
        }

        // Process "other" data and group by type
        if (faction.other && faction.other.length > 0) {
            const groupedByType = {};

            faction.other.forEach(item => {
                const type = (item.type || 'Other').trim();
                if (!groupedByType[type]) {
                    groupedByType[type] = [];
                }
                groupedByType[type].push(item);
            });

            // Sort types alphabetically
            const sortedTypes = Object.keys(groupedByType).sort();

            sortedTypes.forEach(type => {
                // Sort items by points (descending) then by name (alphabetically)
                const sortedItems = groupedByType[type].sort((a, b) => {
                    const pointsA = a.points !== undefined ? a.points : 0;
                    const pointsB = b.points !== undefined ? b.points : 0;

                    if (pointsA !== pointsB) {
                        return pointsB - pointsA; // Sort by points descending (highest first)
                    }

                    // If points are equal, sort alphabetically by name
                    const nameA = (a.name || '').toLowerCase();
                    const nameB = (b.name || '').toLowerCase();
                    return nameA.localeCompare(nameB);
                });

                html += `
                    <div class="table-container">
                        <h4>${type}</h4>
                        <table class="bp-table two-column-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Points</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                sortedItems.forEach((item, index) => {
                    const rowClass = index % 2 === 0 ? 'even-row' : 'odd-row';
                    html += `
                                <tr class="${rowClass}">
                                    <td>${item.name || 'N/A'}</td>
                                    <td>${item.points !== undefined ? item.points : 'N/A'}</td>
                                </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            });
        }

        return html;
    }

    // Helper method to format battle profile names with badges/subtitles
    formatBattleProfileName(profile) {
        let formattedName = profile.name || 'N/A';
        let badges = '';

        // Check for Scourge of Ghyran and replace with badge
        if (formattedName.includes('Scourge of Ghyran')) {
            formattedName = formattedName.replace(/\s*Scourge of Ghyran\s*/g, '').trim();
            badges += '<span class="badge badge-sog">SoG</span>';
        }

        // Split on comma, 'on', or 'with' and create subtitle
        let mainName = formattedName;
        let subtitle = '';

        // Check for splits in order of priority
        const patterns = [
            { separator: ',', keepSeparator: false },
            { separator: ' on ', keepSeparator: true },
            { separator: ' with ', keepSeparator: true }
        ];

        for (const pattern of patterns) {
            if (mainName.includes(pattern.separator)) {
                const parts = mainName.split(pattern.separator);
                mainName = parts[0].trim();
                const subtitleText = parts.slice(1).join(pattern.separator).trim();

                if (subtitleText) {
                    if (pattern.keepSeparator) {
                        subtitle = `<div class="profile-subtitle">${pattern.separator.trim()} ${subtitleText}</div>`;
                    } else {
                        subtitle = `<div class="profile-subtitle">${subtitleText}</div>`;
                    }
                }
                break; // Only split on the first match
            }
        }

        // Add legends badge if applicable
        if (profile.legends === true) {
            badges += '<span class="badge badge-legends">Legends</span>';
        }

        return (badges ? `<div class="badge-row">${badges}</div>` : '') + mainName + subtitle;
    }    // Helper method to format regiment options as bullet list
    formatRegimentOptions(regimentOptions) {
        if (!regimentOptions || regimentOptions.length === 0) {
            return '';
        }

        let html = '<ul class="regiment-options-list">';
        regimentOptions.forEach(option => {
            html += `<li>${this.formatSingleRegimentOption(option)}</li>`;
        });
        html += '</ul>';

        return html;
    }

    // Placeholder function to format a single regiment option
    formatSingleRegimentOption(option) {
        if (!option) {
            return 'Invalid option';
        }

        // Format the amount based on min/max values
        let amount = '';
        if (option.max === -1) {
            amount = 'Any';
        } else if (option.min === option.max) {
            amount = option.min.toString();
        } else {
            amount = `${option.min}-${option.max}`;
        }

        // Collect all possible type descriptions
        let descriptions = [];

        // Handle keywords case: "nonKeywords non-{keyword} + keywords join ' '"
        if (option.keywords && option.keywords.length > 0) {
            let keywordDesc = '';
            if (option.nonKeywords && option.nonKeywords.length > 0) {
                keywordDesc += option.nonKeywords.map(kw => `non-${kw}`).join(' ') + ' ';
            }
            keywordDesc += option.keywords.join(' ');
            descriptions.push(keywordDesc);
        }

        // Handle subhero category case
        if (option.subhero_categories) {
            descriptions.push(...option.subhero_categories);
        }

        // Handle specific unit name case
        if (option.unit_names) {
            descriptions.push(...option.unit_names);
        }

        // Join all descriptions with " or "
        const typeDescription = descriptions.join(' or ');

        return `${amount} ${typeDescription}`;
    }

    // Helper method to format custom notes based on profile data
    formatCustomNotes(profile) {
        let notes = [];

        // Add custom note logic based on profile properties (excluding legends which is now in badges)
        if (profile.requiredLeader) {
            notes.push(`Required Leader: ${profile.requiredLeader}`);
        }
        if (profile.exclusiveWith) {
            notes.push(`This unit and ${profile.exclusiveWith} can not be included in the same army`);
        }

        if (profile.retiringOn) {
            notes.push(`Retiring to legends on: ${profile.retiringOn}`);
        }

        if (profile.undersizeCondition) {
            notes.push(`1 unit of this type can be included for each ${profile.undersizeCondition} in your list`);
        }

        if (!profile.hero) {
            if (profile.unit_size == 1 && profile.reinforceable) {
                notes.push(`This unit can be reinforced`);
            }

            if (profile.unit_size > 1 && !profile.reinforceable) {
                notes.push(`This unit can not be reinforced`);
            }
        }

        if (notes.length === 0) {
            return '';
        }

        let html = '<ul class="custom-notes-list">';
        notes.forEach(note => {
            html += `<li>${note}</li>`;
        });
        html += '</ul>';

        return html;
    }    // Helper method to format relevant keywords
    formatRelevantKeywords(profile) {
        let keywords = profile.keywords || [];

        // TODO: Add keyword extraction logic based on profile properties
        // This might include keywords from abilities, weapon types, unit characteristics, etc.

        if (keywords.length === 0) {
            return '';
        }

        return keywords.join(', ');
    }

    // Render Heroes table with data
    renderHeroesTable(heroes) {
        let html = `
            <div class="table-container">
                <h4>Heroes</h4>
                <table class="bp-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Points</th>
                            <th>Unit Size</th>
                            <th>Regiment Options</th>
                            <th>Sub Hero Category</th>
                            <th>Notes</th>
                            <th>Base Size</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        heroes.forEach((hero, index) => {
            const rowClass = index % 2 === 0 ? 'even-row' : 'odd-row';
            html += `
                        <tr class="${rowClass}">
                            <td>${this.formatBattleProfileName(hero)}</td>
                            <td>${hero.points !== undefined ? hero.points : 'N/A'}</td>
                            <td>${hero.unit_size || 'N/A'}</td>
                            <td>${this.formatRegimentOptions(hero.regiment_options)}</td>
                            <td>${hero.subhero_categories && hero.subhero_categories.length > 0 ? hero.subhero_categories.join(', ') : ''}</td>
                            <td>${this.formatCustomNotes(hero)}</td>
                            <td>${hero.base_size || 'N/A'}</td>
                        </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    // Render Units table with data
    renderUnitsTable(units) {
        let html = `
            <div class="table-container">
                <h4>Units</h4>
                <table class="bp-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Points</th>
                            <th>Unit Size</th>
                            <th>Relevant Keywords</th>
                            <th>Notes</th>
                            <th>Base Size</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        units.forEach((unit, index) => {
            const rowClass = index % 2 === 0 ? 'even-row' : 'odd-row';
            html += `
                        <tr class="${rowClass}">
                            <td>${this.formatBattleProfileName(unit)}</td>
                            <td>${unit.points !== undefined ? unit.points : 'N/A'}</td>
                            <td>${unit.unit_size || 'N/A'}</td>
                            <td>${this.formatRelevantKeywords(unit)}</td>
                            <td>${this.formatCustomNotes(unit)}</td>
                            <td>${unit.base_size || 'N/A'}</td>
                        </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    // Render empty Heroes table placeholder
    renderEmptyHeroesTable() {
        return `
            <div class="table-container">
                <h4>Heroes</h4>
                <table class="bp-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Points</th>
                            <th>Unit Size</th>
                            <th>Regiment Options</th>
                            <th>Sub Hero Category</th>
                            <th>Notes</th>
                            <th>Base Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="even-row">
                            <td colspan="7" style="text-align: center; font-style: italic;">No Heroes data available</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    // Render empty Units table placeholder
    renderEmptyUnitsTable() {
        return `
            <div class="table-container">
                <h4>Units</h4>
                <table class="bp-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Points</th>
                            <th>Unit Size</th>
                            <th>Relevant Keywords</th>
                            <th>Notes</th>
                            <th>Base Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="even-row">
                            <td colspan="6" style="text-align: center; font-style: italic;">No Units data available</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    renderRegimentsOfRenown() {
        if (!this.data || !this.data.data || !this.data.data.regiments_of_renown) {
            return '<p>No Regiments of Renown data available.</p>';
        }

        const regiments = this.data.data.regiments_of_renown;

        let html = `
            <div class="table-container">
                <table class="bp-table regiment-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Points</th>
                            <th>Units</th>
                            <th>Allowed Armies</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        regiments.forEach((regiment, index) => {
            const rowClass = index % 2 === 0 ? 'even-row' : 'odd-row';

            // Format units as bullet list
            let unitsHtml = '<ul class="unit-list">';
            for (const [unitName, count] of Object.entries(regiment.units)) {
                unitsHtml += `<li>${count} x ${unitName}</li>`;
            }
            unitsHtml += '</ul>';

            // Format armies as bullet list, potentially in two columns if long
            let armiesHtml = '<ul class="army-list';
            if (regiment.allowedArmies.length > 6) {
                armiesHtml += ' two-column';
            }
            armiesHtml += '">';

            regiment.allowedArmies.forEach(army => {
                armiesHtml += `<li>${army}</li>`;
            });
            armiesHtml += '</ul>';

            html += `
                        <tr class="${rowClass}">
                            <td>${regiment.name}</td>
                            <td>${regiment.points}</td>
                            <td>${unitsHtml}</td>
                            <td>${armiesHtml}</td>
                        </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    getDataInfo() {
        if (!this.data) {
            return null;
        }

        return {
            title: this.data.title,
            filename: this.data.filename,
            publishedDate: this.data.publishedDate,
            extractedDate: this.data.extractedDate,
            hash: this.data.hash
        };
    }
}

// Global renderer instance
const bpRenderer = new BattleProfileRenderer();

// Function to update tab content
async function updateTabContent(tabName) {
    const tabContent = document.getElementById(tabName);

    if (!bpRenderer.data) {
        await bpRenderer.loadData();
    }

    let content = '';

    switch (tabName) {
        case 'armies':
            content = `
                <h2>Armies</h2>
                ${bpRenderer.renderArmies()}
            `;
            // After rendering armies content, auto-select the first army
            setTimeout(() => {
                const select = document.getElementById('army-select');
                if (select && select.options.length > 1) {
                    select.selectedIndex = 1; // Select first army (index 0 is "-- Choose an Army --")
                    renderSelectedArmy(); // Trigger the army content rendering
                }
            }, 0);
            break;
        case 'regiments':
            content = `
                <h2>Regiments of Renown</h2>
                ${bpRenderer.renderRegimentsOfRenown()}
            `;
            break;
        case 'manifestations':
            content = `
                <h2>Universal Manifestations</h2>
                ${bpRenderer.renderUniversalManifestations()}
            `;
            break;
    }

    tabContent.innerHTML = content;
}

// Initialize data loading when the page loads
document.addEventListener('DOMContentLoaded', async function () {
    await bpRenderer.loadData();

    // Load initial content for the active tab
    updateTabContent('armies');

    // Add data info to the page if available
    const dataInfo = bpRenderer.getDataInfo();
    if (dataInfo) {
        const main = document.querySelector('main');
        const infoDiv = document.createElement('div');
        infoDiv.className = 'data-info';
        infoDiv.innerHTML = `
            <p><small>Data from: ${dataInfo.filename} | Published: ${dataInfo.publishedDate} | Extracted: ${dataInfo.extractedDate}</small></p>
        `;
        main.appendChild(infoDiv);
    }
});

// Function to render selected army content
function renderSelectedArmy() {
    const select = document.getElementById('army-select');
    const contentDiv = document.getElementById('army-content');

    if (!select || !contentDiv) return;

    const selectedArmy = select.value;
    if (!selectedArmy) {
        contentDiv.innerHTML = '<p>Please select an army from the dropdown above.</p>';
        return;
    }

    const content = bpRenderer.renderSelectedArmyContent(selectedArmy);
    contentDiv.innerHTML = content;
}
