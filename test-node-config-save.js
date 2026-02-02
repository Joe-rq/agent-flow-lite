/**
 * Test Node Configuration Save Functionality
 * 
 * This script tests that node configuration values persist after save:
 * - Start node: inputVariable
 * - LLM node: systemPrompt, temperature
 * - Knowledge node: knowledgeBaseId
 * - Condition node: expression
 * - End node: outputVariable
 */

const { chromium } = require('playwright');
const fs = require('fs');

const URL = 'http://localhost:5173/workflow';
const SCREENSHOT_DIR = 'tmp/screenshots';

// Create screenshots directory
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: { recursive: true } });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('🚀 Starting Node Config Save Test...');
  console.log(`📸 Screenshots will be saved to ${SCREENSHOT_DIR}`);

  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();

  // Collect console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      consoleErrors.push(errorText);
      console.log(`❌ Console Error: ${errorText}`);
    } else if (msg.type() === 'warning') {
      console.log(`⚠️  Console Warning: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Navigate to workflow page
    console.log('\n📍 Step 1: Navigating to workflow page...');
    await page.goto(URL, { waitUntil: 'networkidle' });
    await sleep(1000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/01-initial-load.png`, fullPage: true });
    console.log('✅ Page loaded');

    // Step 2: Add each node type
    console.log('\n📍 Step 2: Adding nodes to canvas...');

    const nodeTypes = [
      { type: 'start', label: '开始节点', config: { inputVariable: 'start_var' } },
      { type: 'llm', label: 'LLM 节点', config: { systemPrompt: 'prompt_test', temperature: 0.8 } },
      { type: 'knowledge', label: '知识库节点', config: { knowledgeBaseId: 'kb1' } },
      { type: 'condition', label: '条件节点', config: { expression: "{{step1.output}} === 'yes'" } },
      { type: 'end', label: '结束节点', config: { outputVariable: 'result_var' } }
    ];

    const nodeIds = [];

    for (const node of nodeTypes) {
      console.log(`  - Adding ${node.label}...`);
      // Click on the node item in the panel
      const nodeButton = page.locator(`text=${node.label}`).first();
      await nodeButton.click();
      await sleep(300);

      // Store the ID of the newly created node
      const nodes = await page.evaluate(() => {
        const vueFlowNodes = window.vueFlowNodes || [];
        return vueFlowNodes.map(n => ({ id: n.id, type: n.type, data: n.data }));
      });

      // Find the most recent node of this type
      const nodesOfType = nodes.filter(n => n.type === node.type);
      if (nodesOfType.length > 0) {
        const latestNode = nodesOfType[nodesOfType.length - 1];
        nodeIds.push({ ...node, nodeId: latestNode.id });
        console.log(`    ✅ Node added with ID: ${latestNode.id}`);
      } else {
        console.log(`    ⚠️  Could not find ${node.label} after adding`);
      }
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/02-all-nodes-added.png`, fullPage: true });
    console.log(`✅ All ${nodeIds.length} nodes added`);

    // Step 3: Test config save for each node
    console.log('\n📍 Step 3: Testing configuration save and persistence...');

    for (let i = 0; i < nodeIds.length; i++) {
      const node = nodeIds[i];
      console.log(`\n  Testing ${node.label} (ID: ${node.nodeId})...`);

      // 3a: Click node to open config panel
      console.log(`    3a. Opening config panel...`);
      const nodeElement = page.locator(`[data-nodeid="${node.nodeId}"]`);
      const count = await nodeElement.count();
      if (count === 0) {
        console.log(`    ⚠️  Could not find node element with data-nodeid="${node.nodeId}"`);
        // Try to find node by clicking on it using Vue Flow's internal structure
        await page.evaluate((nodeId) => {
          const nodes = document.querySelectorAll('.vue-flow__node');
          nodes.forEach(n => {
            if (n.__vueParentComponent?.ctx?.id === nodeId) {
              n.click();
            }
          });
        }, node.nodeId);
      } else {
        await nodeElement.click();
      }
      await sleep(500);

      // Check if config panel is visible
      const configPanel = page.locator('.config-panel');
      const isVisible = await configPanel.isVisible();
      if (!isVisible) {
        console.log(`    ⚠️  Config panel not visible, trying alternative approach...`);
        // Try to trigger node click through Vue Flow instance
        await page.evaluate((nodeId) => {
          const instance = window.__vueFlowInstance__;
          if (instance) {
            const nodes = instance.getNodes();
            const node = nodes.find(n => n.id === nodeId);
            if (node) {
              instance.emit('node-click', { node });
            }
          }
        }, node.node.nodeId);
        await sleep(500);
      }
      await page.screenshot({ path: `${SCREENSHOT_DIR}/03-${node.type}-config-panel-open.png`, fullPage: true });

      // 3b: Fill in configuration values
      console.log(`    3b. Filling configuration values...`);
      if (node.type === 'start') {
        const inputVar = page.locator('input[placeholder="例如: user_query"]');
        await inputVar.fill(node.config.inputVariable);
        console.log(`      ✓ Set inputVariable = "${node.config.inputVariable}"`);
      } else if (node.type === 'llm') {
        const systemPrompt = page.locator('textarea[placeholder="输入系统提示词..."]');
        await systemPrompt.fill(node.config.systemPrompt);
        console.log(`      ✓ Set systemPrompt = "${node.config.systemPrompt}"`);

        // Adjust temperature
        const tempSlider = page.locator('input[type="range"]');
        await tempSlider.evaluate((el, val) => el.value = val, node.config.temperature);
        console.log(`      ✓ Set temperature = ${node.config.temperature}`);
      } else if (node.type === 'knowledge') {
        const kbSelect = page.locator('select.form-select');
        const options = await kbSelect.locator('option').allTextContents();
        console.log(`      Available knowledge bases: ${options.slice(0, 3).join(', ')}...`);

        if (options.length > 1) {
          await kbSelect.selectOption({ index: 1 }); // Select first available KB
          const selectedValue = await kbSelect.inputValue();
          node.config.knowledgeBaseId = selectedValue;
          console.log(`      ✓ Selected knowledge base with ID: ${selectedValue}`);
        } else {
          console.log(`      ⚠️  No knowledge bases available, skipping selection`);
        }
      } else if (node.type === 'condition') {
        const exprInput = page.locator('textarea[placeholder*="{{step1.output}}"]');
        await exprInput.fill(node.config.expression);
        console.log(`      ✓ Set expression = "${node.config.expression}"`);
      } else if (node.type === 'end') {
        const outputVar = page.locator('input[placeholder="例如: result"]');
        await outputVar.fill(node.config.outputVariable);
        console.log(`      ✓ Set outputVariable = "${node.config.outputVariable}"`);
      }

      await sleep(300);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/04-${node.type}-config-filled.png`, fullPage: true });

      // 3c: Click Save button
      console.log(`    3c. Saving configuration...`);
      const saveBtn = page.locator('.save-btn').filter({ hasText: '保存' });
      await saveBtn.click();
      await sleep(300);

      // 3d: Close config panel
      console.log(`    3d. Closing config panel...`);
      const closeBtn = page.locator('.close-btn');
      await closeBtn.click();
      await sleep(300);

      // 3e: Reopen the same node to verify persistence
      console.log(`    3e. Reopening node to verify persistence...`);
      await nodeElement.click();
      await sleep(500);

      // 3f: Verify values are persisted
      console.log(`    3f. Verifying persisted values...`);
      let allValuesPersisted = true;

      if (node.type === 'start') {
        const inputVar = page.locator('input[placeholder="例如: user_query"]');
        const value = await inputVar.inputValue();
        const persisted = value === node.config.inputVariable;
        allValuesPersisted = persisted;
        console.log(`      ${persisted ? '✅' : '❌'} inputVariable persisted: "${value}" (expected: "${node.config.inputVariable}")`);
      } else if (node.type === 'llm') {
        const systemPrompt = page.locator('textarea[placeholder="输入系统提示词..."]');
        const promptValue = await systemPrompt.inputValue();
        const promptPersisted = promptValue === node.config.systemPrompt;

        const tempSlider = page.locator('input[type="range"]');
        const tempValue = await tempSlider.inputValue();
        const tempPersisted = parseFloat(tempValue) === node.config.temperature;

        allValuesPersisted = promptPersisted && tempPersisted;
        console.log(`      ${promptPersistPersisted ? '✅' : '❌'} systemPrompt persisted: "${promptValue}"`);
        console.log(`      ${tempPersisted ? '✅' : '❌'} temperature persisted: ${tempValue} (expected: ${node.config.temperature})`);
      } else if (node.type === 'knowledge') {
        const kbSelect = page.locator('select.form-select');
        const selectedValue = await kbSelect.inputValue();
        const persisted = selectedValue === node.config.knowledgeBaseId;
        allValuesPersisted = persisted;
        console.log(`      ${persisted ? '✅' : '❌'} knowledgeBaseId persisted: "${selectedValue}"`);
      } else if (node.type === 'condition') {
        const exprInput = page.locator('textarea[placeholder*="{{step1.output}}"]');
        const value = await exprInput.inputValue();
        const persisted = value === node.config.expression;
        allValuesPersisted = persisted;
        console.log(`      ${persisted ? '✅' : '❌'} expression persisted: "${value}"`);
      } else if (node.type === 'end') {
        const outputVar = page.locator('input[placeholder="例如: result"]');
        const value = await outputVar.inputValue();
        const persisted = value === node.config.outputVariable;
        allValuesPersisted = persisted;
        console.log(`      ${persisted ? '✅' : '❌'} outputVariable persisted: "${value}"`);
      }

      if (allValuesPersisted) {
        console.log(`    ✅ ${node.label} config save and persist: PASS`);
      } else {
        console.log(`    ❌ ${node.label} config save and persist: FAIL`);
      }

      await page.screenshot({ path: `${SCREENSHOT_DIR}/05-${node.type()}-verify-persistence.png`, fullPage: true });

      // Close panel
      await closeBtn.click();
      await sleep(300);
    }

    // Final screenshot
    await page.screenshot({ path: `${SCREENSHOT_DIR}/06-final-state.png`, fullPage: true });

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`✅ Nodes tested: ${nodeIds.length}`);
    console.log(`❌ Console errors: ${consoleErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\n⚠️  Console Errors:');
      consoleErrors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err}`);
      });
    }

    console.log(`\n📸 Screenshots saved to: ${SCREENSHOT_DIR}/`);
    console.log('\n🎉 Test completed!');

  } catch (error) {
    console.error('\n❌ Test failed with error:', error);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/error-state.png`, fullPage: true });
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
