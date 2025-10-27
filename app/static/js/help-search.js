/**
 * EU Trip Tracker - Searchable Help Documentation
 * Phase 3 Implementation: Advanced search and filtering for help content
 */

class HelpSearch {
    constructor() {
        this.searchIndex = new Map();
        this.searchResults = [];
        this.currentQuery = '';
        this.searchInput = null;
        this.resultsContainer = null;
        this.noResultsElement = null;
        
        this.init();
    }

    init() {
        this.createSearchInterface();
        this.buildSearchIndex();
        this.bindEvents();
    }

    createSearchInterface() {
        // Add search bar to help page if it doesn't exist
        const helpHeader = document.querySelector('.help-header');
        if (helpHeader && !document.querySelector('.help-search-container')) {
            const searchContainer = document.createElement('div');
            searchContainer.className = 'help-search-container';
            searchContainer.style.cssText = `
                margin: 20px 0;
                position: relative;
            `;

            searchContainer.innerHTML = `
                <div style="position: relative; max-width: 500px; margin: 0 auto;">
                    <input type="text" 
                           id="helpSearchInput" 
                           placeholder="Search help documentation..." 
                           style="
                               width: 100%;
                               padding: 12px 16px 12px 44px;
                               border: 2px solid #e5e7eb;
                               border-radius: 8px;
                               font-size: 16px;
                               outline: none;
                               transition: border-color 0.2s;
                           "
                           onfocus="this.style.borderColor='#4C739F'"
                           onblur="this.style.borderColor='#e5e7eb'">
                    <svg style="
                        position: absolute;
                        left: 14px;
                        top: 50%;
                        transform: translateY(-50%);
                        width: 20px;
                        height: 20px;
                        color: #6b7280;
                    " viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="M21 21l-4.35-4.35"></path>
                    </svg>
                    <button id="clearSearch" style="
                        position: absolute;
                        right: 12px;
                        top: 50%;
                        transform: translateY(-50%);
                        background: none;
                        border: none;
                        color: #6b7280;
                        cursor: pointer;
                        display: none;
                        padding: 4px;
                    " onclick="helpSearch.clearSearch()">×</button>
                </div>
                <div id="searchResults" style="
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    display: none;
                    max-height: 400px;
                    overflow-y: auto;
                "></div>
            `;

            helpHeader.parentNode.insertBefore(searchContainer, helpHeader.nextSibling);
            
            this.searchInput = document.getElementById('helpSearchInput');
            this.resultsContainer = document.getElementById('searchResults');
            this.clearButton = document.getElementById('clearSearch');
        }
    }

    buildSearchIndex() {
        // Index all help content
        const sections = document.querySelectorAll('.help-section');
        sections.forEach((section, index) => {
            const title = section.querySelector('.help-section-title h3')?.textContent || '';
            const content = section.querySelector('.help-section-body')?.textContent || '';
            const sectionId = section.querySelector('.help-section-header')?.onclick?.toString() || '';
            
            // Create searchable content
            const searchableContent = {
                id: `section-${index}`,
                title: title,
                content: content,
                element: section,
                keywords: this.extractKeywords(title + ' ' + content),
                type: 'section'
            };
            
            this.searchIndex.set(searchableContent.id, searchableContent);
        });

        // Index quick tips
        const tips = document.querySelectorAll('.quick-tip');
        tips.forEach((tip, index) => {
            const title = tip.querySelector('h4')?.textContent || '';
            const content = tip.querySelector('p')?.textContent || '';
            
            const searchableContent = {
                id: `tip-${index}`,
                title: title,
                content: content,
                element: tip,
                keywords: this.extractKeywords(title + ' ' + content),
                type: 'tip'
            };
            
            this.searchIndex.set(searchableContent.id, searchableContent);
        });

        // Add common help topics
        this.addCommonTopics();
    }

    addCommonTopics() {
        const commonTopics = [
            {
                id: '90-180-rule',
                title: '90/180 Day Rule',
                content: 'UK citizens can spend up to 90 days in the Schengen Area within any 180-day period. This is a rolling window that moves every day.',
                keywords: ['90', '180', 'rule', 'schengen', 'limit', 'days', 'rolling', 'window'],
                type: 'topic'
            },
            {
                id: 'compliance-status',
                title: 'Compliance Status',
                content: 'Green = Safe (30+ days), Amber = Caution (10-29 days), Red = At Risk (<10 days or over limit).',
                keywords: ['status', 'compliance', 'green', 'amber', 'red', 'safe', 'caution', 'risk'],
                type: 'topic'
            },
            {
                id: 'adding-trips',
                title: 'Adding Trips',
                content: 'Three methods: Individual trips, Bulk trips, Excel import. All require departure date, return date, and destination country.',
                keywords: ['add', 'trip', 'individual', 'bulk', 'excel', 'import', 'date', 'country'],
                type: 'topic'
            },
            {
                id: 'forecasting',
                title: 'Trip Forecasting',
                content: 'Plan future trips and see their impact on compliance before booking. Shows days used, remaining days, and risk assessment.',
                keywords: ['forecast', 'planning', 'future', 'impact', 'risk', 'assessment', 'days'],
                type: 'topic'
            },
            {
                id: 'export-data',
                title: 'Exporting Data',
                content: 'Generate CSV reports for HR records or PDF summaries. Supports custom date ranges and employee selection.',
                keywords: ['export', 'csv', 'pdf', 'report', 'data', 'hr', 'records'],
                type: 'topic'
            },
            {
                id: 'privacy-gdpr',
                title: 'Privacy & GDPR',
                content: 'Fully GDPR-compliant system with data export, deletion, and access controls. All data is encrypted and secure.',
                keywords: ['privacy', 'gdpr', 'data', 'export', 'delete', 'secure', 'encrypted'],
                type: 'topic'
            }
        ];

        commonTopics.forEach(topic => {
            this.searchIndex.set(topic.id, topic);
        });
    }

    extractKeywords(text) {
        // Simple keyword extraction
        const words = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 2)
            .filter(word => !this.isStopWord(word));
        
        // Remove duplicates
        return [...new Set(words)];
    }

    isStopWord(word) {
        const stopWords = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'a', 'an'];
        return stopWords.includes(word);
    }

    bindEvents() {
        if (!this.searchInput) return;

        // Search input events
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        this.searchInput.addEventListener('focus', () => {
            if (this.searchResults.length > 0) {
                this.resultsContainer.style.display = 'block';
            }
        });

        // Click outside to close results
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.help-search-container')) {
                this.resultsContainer.style.display = 'none';
            }
        });

        // Keyboard navigation
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (this.searchResults.length > 0) {
                    this.navigateToResult(this.searchResults[0]);
                }
            }
        });
    }

    handleSearch(query) {
        this.currentQuery = query.trim();
        
        if (this.currentQuery.length === 0) {
            this.clearSearch();
            return;
        }

        // Show clear button
        this.clearButton.style.display = 'block';

        // Perform search
        this.searchResults = this.performSearch(this.currentQuery);
        this.displayResults();
    }

    performSearch(query) {
        const results = [];
        const queryWords = this.extractKeywords(query);
        
        this.searchIndex.forEach((item, id) => {
            let score = 0;
            
            // Title matches (higher weight)
            queryWords.forEach(word => {
                if (item.title.toLowerCase().includes(word)) {
                    score += 3;
                }
                if (item.keywords.includes(word)) {
                    score += 2;
                }
                if (item.content.toLowerCase().includes(word)) {
                    score += 1;
                }
            });
            
            if (score > 0) {
                results.push({
                    ...item,
                    score: score,
                    matchedWords: queryWords.filter(word => 
                        item.title.toLowerCase().includes(word) || 
                        item.content.toLowerCase().includes(word)
                    )
                });
            }
        });
        
        // Sort by score (highest first)
        return results.sort((a, b) => b.score - a.score);
    }

    displayResults() {
        if (this.searchResults.length === 0) {
            this.resultsContainer.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #6b7280;">
                    <svg style="width: 40px; height: 40px; margin-bottom: 12px; color: #d1d5db;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="M21 21l-4.35-4.35"></path>
                    </svg>
                    <div>No results found for "${this.currentQuery}"</div>
                    <div style="font-size: 14px; margin-top: 4px;">Try different keywords or check spelling</div>
                </div>
            `;
        } else {
            const resultsHtml = this.searchResults.slice(0, 10).map(result => {
                const highlightedTitle = this.highlightMatches(result.title, this.currentQuery);
                const highlightedContent = this.highlightMatches(
                    result.content.substring(0, 150) + (result.content.length > 150 ? '...' : ''),
                    this.currentQuery
                );
                
                return `
                    <div class="search-result-item" 
                         style="
                             padding: 12px 16px;
                             border-bottom: 1px solid #f3f4f6;
                             cursor: pointer;
                             transition: background-color 0.2s;
                         "
                         onmouseover="this.style.backgroundColor='#f9fafb'"
                         onmouseout="this.style.backgroundColor='white'"
                         onclick="helpSearch.navigateToResult('${result.id}')">
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 4px;">
                            ${highlightedTitle}
                        </div>
                        <div style="color: #6b7280; font-size: 14px; line-height: 1.4;">
                            ${highlightedContent}
                        </div>
                        <div style="
                            margin-top: 4px;
                            font-size: 12px;
                            color: #9ca3af;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        ">${result.type}</div>
                    </div>
                `;
            }).join('');
            
            this.resultsContainer.innerHTML = resultsHtml;
        }
        
        this.resultsContainer.style.display = 'block';
    }

    highlightMatches(text, query) {
        if (!query) return text;
        
        const queryWords = query.split(/\s+/).filter(word => word.length > 0);
        let highlightedText = text;
        
        queryWords.forEach(word => {
            const regex = new RegExp(`(${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark style="background: #fef3c7; padding: 1px 2px; border-radius: 2px;">$1</mark>');
        });
        
        return highlightedText;
    }

    navigateToResult(resultId) {
        const result = this.searchIndex.get(resultId);
        if (!result) return;
        
        // Close search results
        this.resultsContainer.style.display = 'none';
        this.searchInput.value = '';
        this.clearButton.style.display = 'none';
        
        if (result.element) {
            // Scroll to element and highlight
            result.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add temporary highlight
            result.element.style.transition = 'all 0.3s ease';
            result.element.style.backgroundColor = '#fef3c7';
            result.element.style.borderRadius = '8px';
            result.element.style.padding = '8px';
            
            setTimeout(() => {
                result.element.style.backgroundColor = '';
                result.element.style.borderRadius = '';
                result.element.style.padding = '';
            }, 3000);
            
            // Expand section if it's collapsible
            const sectionHeader = result.element.querySelector('.help-section-header');
            if (sectionHeader && !sectionHeader.classList.contains('active')) {
                sectionHeader.click();
            }
        } else {
            // For common topics, show in a modal
            this.showTopicModal(result);
        }
    }

    showTopicModal(topic) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                margin: 20px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="margin: 0; color: #1f2937;">${topic.title}</h3>
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #6b7280;
                    ">×</button>
                </div>
                <div style="color: #4b5563; line-height: 1.6; margin-bottom: 20px;">${topic.content}</div>
                <div style="text-align: right;">
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="
                        background: #4C739F;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 6px;
                        cursor: pointer;
                    ">Got it!</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    clearSearch() {
        this.searchInput.value = '';
        this.resultsContainer.style.display = 'none';
        this.clearButton.style.display = 'none';
        this.searchResults = [];
        this.currentQuery = '';
    }
}

// Initialize help search when DOM is loaded
let helpSearch;
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on help page
    if (document.querySelector('.help-header')) {
        helpSearch = new HelpSearch();
        window.helpSearch = helpSearch;
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HelpSearch;
}
