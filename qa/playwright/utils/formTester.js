/**
 * Form Testing Utility for ComplyEur
 * 
 * Automatically fills and submits forms with safe dummy data
 */

class FormTester {
  constructor(page) {
    this.page = page;
    this.results = [];
  }

  /**
   * Generate dummy data based on field type and name
   */
  getDummyValue(field) {
    const name = (field.name || field.id || '').toLowerCase();
    const type = (field.type || '').toLowerCase();

    // Password fields
    if (type === 'password' || name.includes('password')) {
      return 'TestPassword123!';
    }

    // Email fields
    if (type === 'email' || name.includes('email')) {
      return 'test@example.com';
    }

    // Date fields
    if (type === 'date' || name.includes('date')) {
      const today = new Date();
      const futureDate = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
      return futureDate.toISOString().split('T')[0];
    }

    // Number fields
    if (type === 'number' || name.includes('count') || name.includes('age')) {
      return '25';
    }

    // Employee/person name fields
    if (name.includes('name') || name.includes('employee')) {
      return 'Test User QA';
    }

    // Country fields
    if (name.includes('country')) {
      return 'France';
    }

    // Purpose/description fields
    if (name.includes('purpose') || name.includes('description') || name.includes('notes')) {
      return 'QA Automated Test Entry';
    }

    // Job reference fields
    if (name.includes('job') || name.includes('ref')) {
      return 'QA-TEST-001';
    }

    // Checkbox
    if (type === 'checkbox') {
      return true;
    }

    // Radio
    if (type === 'radio') {
      return true;
    }

    // Select dropdown - return first non-empty option
    if (type === 'select' && field.options && field.options.length > 0) {
      const validOption = field.options.find(opt => opt.value && opt.value !== '');
      return validOption ? validOption.value : field.options[0].value;
    }

    // Default text value
    return 'Test Data QA';
  }

  /**
   * Fill a single form field
   */
  async fillField(field) {
    try {
      const selector = field.selector || `[name="${field.name}"]`;
      const element = await this.page.$(selector);

      if (!element) {
        console.log(`  ⚠ Field not found: ${field.name || field.id}`);
        return false;
      }

      const type = field.type.toLowerCase();

      if (type === 'select' || type === 'select-one') {
        const value = this.getDummyValue(field);
        await this.page.selectOption(selector, value);
        console.log(`  ✓ Selected: ${field.name} = ${value}`);
      } else if (type === 'checkbox' || type === 'radio') {
        await this.page.check(selector);
        console.log(`  ✓ Checked: ${field.name}`);
      } else if (type === 'textarea' || type === 'text' || type === 'email' || type === 'password' || type === 'date' || type === 'number') {
        const value = this.getDummyValue(field);
        await this.page.fill(selector, String(value));
        console.log(`  ✓ Filled: ${field.name} = ${value}`);
      }

      return true;
    } catch (error) {
      console.error(`  ✗ Error filling field ${field.name}: ${error.message}`);
      return false;
    }
  }

  /**
   * Test a single form
   */
  async testForm(formInfo, options = {}) {
    const { submit = true, screenshot = true } = options;

    console.log(`\nTesting form: ${formInfo.id || formInfo.action}`);
    console.log(`  Method: ${formInfo.method}`);
    console.log(`  Fields: ${formInfo.fields.length}`);

    const result = {
      form: formInfo.id || formInfo.action,
      success: false,
      fieldsFilled: 0,
      errors: []
    };

    try {
      // Fill each field
      for (const field of formInfo.fields) {
        // Skip hidden and submit buttons
        if (field.type === 'hidden' || field.type === 'submit' || field.type === 'button') {
          continue;
        }

        const filled = await this.fillField(field);
        if (filled) {
          result.fieldsFilled++;
        }
      }

      // Take screenshot before submission
      if (screenshot) {
        const screenshotPath = `screenshots/form-${formInfo.id || 'unnamed'}-filled.png`;
        await this.page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`  📸 Screenshot saved: ${screenshotPath}`);
      }

      // Submit form if requested
      if (submit) {
        console.log(`  → Submitting form...`);
        
        // Wait for any navigation or network activity
        const [response] = await Promise.all([
          this.page.waitForResponse(response => response.request().method() === 'POST', { timeout: 5000 }).catch(() => null),
          this.page.click(`${formInfo.selector} input[type="submit"], ${formInfo.selector} button[type="submit"]`).catch(() => {
            // Fallback: try Enter key on last field
            return this.page.keyboard.press('Enter');
          })
        ]);

        // Wait for any response
        await this.page.waitForTimeout(1000);

        // Check for errors on the page
        const hasError = await this.page.evaluate(() => {
          return document.body.textContent.includes('error') || 
                 document.body.textContent.includes('Error') ||
                 document.querySelector('.error, .alert-danger');
        });

        if (hasError) {
          console.log(`  ⚠ Form submission showed error message`);
          result.errors.push('Error message displayed after submission');
        } else {
          console.log(`  ✓ Form submitted successfully`);
          result.success = true;
        }

        // Take screenshot after submission
        if (screenshot) {
          const screenshotPath = `screenshots/form-${formInfo.id || 'unnamed'}-submitted.png`;
          await this.page.screenshot({ path: screenshotPath, fullPage: true });
        }
      }

    } catch (error) {
      console.error(`  ✗ Error testing form: ${error.message}`);
      result.errors.push(error.message);
    }

    this.results.push(result);
    return result;
  }

  /**
   * Test all forms on the current page
   */
  async testAllForms(options = {}) {
    const forms = await this.page.evaluate(() => {
      const formsList = [];
      document.querySelectorAll('form').forEach((form, index) => {
        const fields = [];
        form.querySelectorAll('input, textarea, select').forEach(field => {
          fields.push({
            type: field.type || field.tagName.toLowerCase(),
            name: field.name,
            id: field.id,
            required: field.required,
            selector: field.id ? `#${field.id}` : `[name="${field.name}"]`,
            options: field.tagName.toLowerCase() === 'select' 
              ? Array.from(field.options).map(opt => ({ value: opt.value, text: opt.textContent }))
              : undefined
          });
        });

        formsList.push({
          action: form.getAttribute('action') || window.location.pathname,
          method: form.getAttribute('method') || 'GET',
          id: form.id || `form-${index}`,
          selector: form.id ? `#${form.id}` : `form:nth-of-type(${index + 1})`,
          fields: fields
        });
      });
      return formsList;
    });

    console.log(`\nFound ${forms.length} form(s) on page`);

    for (const form of forms) {
      await this.testForm(form, options);
      
      // Reload page between forms to reset state
      if (forms.indexOf(form) < forms.length - 1) {
        await this.page.reload({ waitUntil: 'networkidle' });
      }
    }

    return this.results;
  }

  /**
   * Get test results
   */
  getResults() {
    return {
      totalForms: this.results.length,
      successfulForms: this.results.filter(r => r.success).length,
      failedForms: this.results.filter(r => !r.success).length,
      results: this.results
    };
  }
}

module.exports = FormTester;

