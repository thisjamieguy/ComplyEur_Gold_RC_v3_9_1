/**
 * Recursive Site Crawler for ComplyEur
 * 
 * Discovers and tests all pages, links, and interactive elements
 */

const fs = require('fs');
const path = require('path');

class SiteCrawler {
  constructor(page, options = {}) {
    this.page = page;
    this.visitedUrls = new Set();
    this.discoveredUrls = new Set();
    this.errors = [];
    this.consoleErrors = [];
    this.brokenLinks = [];
    this.baseUrl = options.baseUrl || 'http://localhost:5001';
    this.maxDepth = options.maxDepth || 5;
    this.currentDepth = 0;
    
    // Listen to console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        this.consoleErrors.push({
          url: page.url(),
          message: msg.text(),
          timestamp: new Date().toISOString()
        });
      }
    });

    // Listen to page errors
    page.on('pageerror', error => {
      this.errors.push({
        url: page.url(),
        error: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      });
    });
  }

  /**
   * Extract all clickable elements from the current page
   */
  async extractLinks() {
    return await this.page.evaluate(() => {
      const links = [];
      
      // Get all <a> tags
      document.querySelectorAll('a[href]').forEach(el => {
        const href = el.getAttribute('href');
        if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
          links.push({
            type: 'link',
            href: href,
            text: el.textContent.trim().substring(0, 100),
            selector: el.id ? `#${el.id}` : `a[href="${href}"]`
          });
        }
      });

      // Get all buttons
      document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach((el, index) => {
        const onclick = el.getAttribute('onclick');
        const formAction = el.form ? el.form.getAttribute('action') : null;
        
        links.push({
          type: 'button',
          text: el.textContent.trim() || el.value || `Button ${index}`,
          onclick: onclick,
          formAction: formAction,
          selector: el.id ? `#${el.id}` : `button:nth-of-type(${index + 1})`
        });
      });

      // Get all forms
      document.querySelectorAll('form').forEach((form, index) => {
        links.push({
          type: 'form',
          action: form.getAttribute('action') || window.location.pathname,
          method: form.getAttribute('method') || 'GET',
          id: form.id || `form-${index}`,
          selector: form.id ? `#${form.id}` : `form:nth-of-type(${index + 1})`
        });
      });

      return links;
    });
  }

  /**
   * Extract all forms and their fields
   */
  async extractForms() {
    return await this.page.evaluate(() => {
      const forms = [];
      
      document.querySelectorAll('form').forEach((form, formIndex) => {
        const fields = [];
        
        // Get all input fields
        form.querySelectorAll('input, textarea, select').forEach((field, fieldIndex) => {
          const fieldInfo = {
            type: field.type || field.tagName.toLowerCase(),
            name: field.name,
            id: field.id,
            required: field.required,
            selector: field.id ? `#${field.id}` : `${field.tagName.toLowerCase()}[name="${field.name}"]`
          };

          // For select elements, get options
          if (field.tagName.toLowerCase() === 'select') {
            fieldInfo.options = Array.from(field.options).map(opt => ({
              value: opt.value,
              text: opt.textContent
            }));
          }

          fields.push(fieldInfo);
        });

        forms.push({
          action: form.getAttribute('action') || window.location.pathname,
          method: form.getAttribute('method') || 'GET',
          id: form.id || `form-${formIndex}`,
          selector: form.id ? `#${form.id}` : `form:nth-of-type(${formIndex + 1})`,
          fields: fields
        });
      });

      return forms;
    });
  }

  /**
   * Normalize URL to absolute form
   */
  normalizeUrl(url) {
    if (!url) return null;
    
    // Remove query strings and fragments for deduplication
    const urlObj = new URL(url, this.baseUrl);
    
    // Only crawl same domain
    if (!urlObj.href.startsWith(this.baseUrl)) {
      return null;
    }

    // Remove query string and fragment
    return `${urlObj.origin}${urlObj.pathname}`;
  }

  /**
   * Check if URL should be crawled
   */
  shouldCrawl(url) {
    if (!url) return false;
    
    const normalized = this.normalizeUrl(url);
    if (!normalized) return false;
    
    // Skip if already visited
    if (this.visitedUrls.has(normalized)) return false;
    
    // Skip static files
    if (normalized.match(/\.(css|js|jpg|jpeg|png|gif|svg|pdf|zip|webp)$/i)) return false;
    
    // Skip logout to maintain session
    if (normalized.includes('/logout')) return false;
    
    return true;
  }

  /**
   * Visit a URL and check for errors
   */
  async visitUrl(url, depth = 0) {
    const normalized = this.normalizeUrl(url);
    
    if (!this.shouldCrawl(normalized) || depth > this.maxDepth) {
      return;
    }

    console.log(`[Depth ${depth}] Visiting: ${normalized}`);
    this.visitedUrls.add(normalized);

    try {
      const response = await this.page.goto(normalized, {
        waitUntil: 'networkidle',
        timeout: 15000
      });

      const status = response.status();
      
      // Check for server errors
      if (status >= 500) {
        this.errors.push({
          url: normalized,
          error: `Server Error: ${status}`,
          timestamp: new Date().toISOString()
        });
        console.error(`  ✗ Server Error ${status} on ${normalized}`);
        return;
      }

      // Check for 404s
      if (status === 404) {
        this.brokenLinks.push({
          url: normalized,
          status: 404,
          timestamp: new Date().toISOString()
        });
        console.warn(`  ⚠ 404 Not Found: ${normalized}`);
        return;
      }

      console.log(`  ✓ Status ${status}`);

      // Wait for page to be fully loaded
      await this.page.waitForLoadState('domcontentloaded');
      await this.page.waitForTimeout(500); // Small delay for JS to execute

      // Extract links for further crawling
      const links = await this.extractLinks();
      
      for (const link of links) {
        if (link.type === 'link' && link.href) {
          const fullUrl = new URL(link.href, normalized).href;
          const normalizedLink = this.normalizeUrl(fullUrl);
          
          if (normalizedLink && !this.visitedUrls.has(normalizedLink)) {
            this.discoveredUrls.add(normalizedLink);
          }
        }
      }

    } catch (error) {
      this.errors.push({
        url: normalized,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      console.error(`  ✗ Error visiting ${normalized}: ${error.message}`);
    }
  }

  /**
   * Crawl the entire site starting from a URL
   */
  async crawl(startUrl, depth = 0) {
    await this.visitUrl(startUrl, depth);

    // Visit all discovered URLs at the next depth level
    if (depth < this.maxDepth) {
      const urlsToCrawl = Array.from(this.discoveredUrls).filter(url => !this.visitedUrls.has(url));
      
      for (const url of urlsToCrawl) {
        await this.crawl(url, depth + 1);
      }
    }
  }

  /**
   * Get crawl results
   */
  getResults() {
    return {
      visitedUrls: Array.from(this.visitedUrls),
      totalPages: this.visitedUrls.size,
      errors: this.errors,
      consoleErrors: this.consoleErrors,
      brokenLinks: this.brokenLinks,
      hasErrors: this.errors.length > 0 || this.consoleErrors.length > 0 || this.brokenLinks.length > 0
    };
  }

  /**
   * Save results to file
   */
  saveResults(outputPath) {
    const results = this.getResults();
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    console.log(`\nCrawl results saved to: ${outputPath}`);
    return results;
  }
}

module.exports = SiteCrawler;

