/**
 * Aero-Code ProofLoop Real-Time Dashboard Client
 */

document.addEventListener('DOMContentLoaded', () => {
  const connectionStatus = document.getElementById('connection-status');
  const connectionLabel = document.getElementById('connection-label');
  const terminalLogs = document.getElementById('terminal-logs');
  const btnClearLogs = document.getElementById('btn-clear-logs');
  const runForm = document.getElementById('run-form');
  const btnRunLoop = document.getElementById('btn-run-loop');
  const stepperMode = document.getElementById('stepper-mode');
  const verdictBadge = document.getElementById('verdict-badge');
  const diffContent = document.getElementById('diff-content');
  const citationsList = document.getElementById('citations-list');
  const patchFileLabel = document.getElementById('patch-file-label');

  // Presets
  const btnPresetPydantic = document.getElementById('btn-preset-pydantic');
  const btnPresetRequests = document.getElementById('btn-preset-requests');
  const btnPresetPaypal = document.getElementById('btn-preset-paypal');
  const issueTitleInput = document.getElementById('issue-title');
  const targetPkgInput = document.getElementById('target-package');
  const pkgVersionInput = document.getElementById('package-version');
  const tracebackInput = document.getElementById('issue-traceback');
  let selectedCase = 'pydantic_v2_migration';
  let currentRunId = null;
  let lastSequence = 0;
  let submitting = false;
  const visitedPhases = new Set();

  const PIPELINE_PHASES = [
    'INTAKE',
    'INVESTIGATE',
    'RESEARCH',
    'REPRODUCE_BASELINE',
    'GENERATE_PATCH',
    'GIT_GUARD',
    'SANDBOX_EXECUTE',
    'EVIDENCE_REPORT',
    'PUBLISH_PR'
  ];

  // Presets data
  const PRESETS = {
    pydantic: {
      title: "Pydantic V2: parse_obj AttributeError",
      package: "pydantic",
      version: "2.6.1",
      traceback: "AttributeError: type object 'UserModel' has no attribute 'parse_obj'"
    },
    requests: {
      title: "requests.get() missing timeout kwarg causes indefinite hang",
      package: "requests",
      version: "2.31.0",
      traceback: "requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected())"
    },
    paypal: {
      title: "PayPal Webhook Verification: Missing transmission headers causes verification failure",
      package: "paypalrestsdk",
      version: "1.13.3",
      traceback: "PayPalWebhookVerificationError: Missing required PayPal transmission headers: PAYPAL-TRANSMISSION-SIG, PAYPAL-CERT-URL, PAYPAL-TRANSMISSION-TIME"
    }
  };

  function updatePresetAccessibility() {
    [btnPresetPydantic, btnPresetRequests, btnPresetPaypal].forEach(button => {
      button.setAttribute('aria-pressed', String(button.classList.contains('active')));
    });
  }
  updatePresetAccessibility();

  btnPresetPydantic.addEventListener('click', () => {
    selectedCase = 'pydantic_v2_migration';
    btnPresetPydantic.classList.add('active');
    btnPresetRequests.classList.remove('active');
    btnPresetPaypal.classList.remove('active');
    issueTitleInput.value = PRESETS.pydantic.title;
    targetPkgInput.value = PRESETS.pydantic.package;
    pkgVersionInput.value = PRESETS.pydantic.version;
    tracebackInput.value = PRESETS.pydantic.traceback;
    updatePresetAccessibility();
  });

  btnPresetRequests.addEventListener('click', () => {
    selectedCase = 'requests_timeout_kwarg';
    btnPresetRequests.classList.add('active');
    btnPresetPydantic.classList.remove('active');
    btnPresetPaypal.classList.remove('active');
    issueTitleInput.value = PRESETS.requests.title;
    targetPkgInput.value = PRESETS.requests.package;
    pkgVersionInput.value = PRESETS.requests.version;
    tracebackInput.value = PRESETS.requests.traceback;
    updatePresetAccessibility();
  });

  btnPresetPaypal.addEventListener('click', () => {
    selectedCase = 'paypal_webhook_signature';
    btnPresetPaypal.classList.add('active');
    btnPresetPydantic.classList.remove('active');
    btnPresetRequests.classList.remove('active');
    issueTitleInput.value = PRESETS.paypal.title;
    targetPkgInput.value = PRESETS.paypal.package;
    pkgVersionInput.value = PRESETS.paypal.version;
    tracebackInput.value = PRESETS.paypal.traceback;
    updatePresetAccessibility();
  });

  function appendLog(text, type = 'system') {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    line.textContent = `[${timestamp}] ${text}`;
    terminalLogs.appendChild(line);
    if (terminalLogs.children.length > 500) terminalLogs.firstElementChild.remove();
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }

  btnClearLogs.addEventListener('click', () => {
    terminalLogs.innerHTML = '';
    appendLog('Log cleared by user.', 'system');
  });

  function setStepperPhase(currentPhase) {
    if (currentPhase === 'COMPLETED' || currentPhase === 'FAILED') {
      PIPELINE_PHASES.forEach(phase => {
        const node = document.getElementById(`step-${phase}`);
        node.classList.toggle('completed', currentPhase === 'COMPLETED' && visitedPhases.has(phase));
        node.classList.toggle('failed', currentPhase === 'FAILED' && node.classList.contains('active'));
        node.classList.remove('active');
        if (node.nextElementSibling?.classList.contains('step-line')) {
          node.nextElementSibling.classList.toggle('completed', node.classList.contains('completed'));
        }
      });
      stepperMode.textContent = currentPhase;
      return;
    }
    if (!PIPELINE_PHASES.includes(currentPhase)) return;
    visitedPhases.add(currentPhase);
    let passedCurrent = false;
    PIPELINE_PHASES.forEach(phase => {
      const node = document.getElementById(`step-${phase}`);
      if (!node) return;
      node.classList.remove('failed');

      if (phase === currentPhase) {
        node.classList.add('active');
        node.classList.remove('completed');
        passedCurrent = true;
      } else if (!passedCurrent) {
        node.classList.remove('active');
        node.classList.add('completed');
      } else {
        node.classList.remove('active');
        node.classList.remove('completed');
      }
      if (node.nextElementSibling?.classList.contains('step-line')) {
        node.nextElementSibling.classList.toggle('completed', node.classList.contains('completed'));
      }
    });
    stepperMode.textContent = currentPhase;
  }

  function resetMatrix() {
    visitedPhases.clear();
    document.querySelectorAll('.step-node, .step-line').forEach(node => {
      node.classList.remove('active', 'completed', 'failed');
    });
    patchFileLabel.textContent = 'None';
    diffContent.textContent = '// Proposed patch diff will appear here in real time...';
    citationsList.replaceChildren();
    const empty = document.createElement('li');
    empty.className = 'empty-citations';
    empty.textContent = 'No citations fetched yet.';
    citationsList.appendChild(empty);
    ['repro', 'fix', 'regression', 'gitguard'].forEach(id => {
      const pill = document.getElementById(`status-${id}`);
      if (pill) {
        pill.textContent = 'PENDING';
        pill.className = 'matrix-status-pill pending';
      }
    });
    verdictBadge.textContent = 'RUNNING';
    verdictBadge.className = 'verdict-tag';
  }

  function setRunning(running) {
    btnRunLoop.disabled = running;
    btnRunLoop.textContent = running ? 'Running...' : 'Run ProofLoop';
    runForm.setAttribute('aria-busy', String(running));
    [btnPresetPydantic, btnPresetRequests, btnPresetPaypal,
      issueTitleInput, targetPkgInput, pkgVersionInput, tracebackInput].forEach(el => {
      el.disabled = running;
    });
  }

  function renderReport(report) {
    updateMatrixItem('repro', !report.baseline_test_passed);
    updateMatrixItem('fix', report.patched_test_passed);
    updateMatrixItem('regression', report.baseline_suite_passed);
    updateMatrixItem('gitguard', report.git_guard_passed);
    if (report.patch) renderPatch(report.patch);
    renderCitations(report.citations || []);
    verdictBadge.textContent = report.verdict;
    verdictBadge.className = `verdict-tag ${report.verdict.toLowerCase()}`;
  }

  function renderPatch(patch) {
    patchFileLabel.textContent = patch.diffs?.map(diff => diff.file_path).join(', ') || 'Regression test';
    diffContent.textContent = (patch.diffs || []).map(diff =>
      `--- ${diff.file_path} (before)\n+++ ${diff.file_path} (after)\n- ${diff.old_content}\n+ ${diff.new_content}`
    ).join('\n\n') + `\n\n# Isolated Regression Test: ${patch.regression_test_file}\n${patch.regression_test_code}`;
  }

  function renderCitations(citations) {
    citationsList.replaceChildren();
    if (!citations.length) {
      const empty = document.createElement('li');
      empty.className = 'empty-citations';
      empty.textContent = 'No citations available for this run.';
      citationsList.appendChild(empty);
      return;
    }
    citations.forEach(citation => {
      const li = document.createElement('li');
      const title = document.createElement('strong');
      title.textContent = citation.title;
      li.append(title, document.createElement('br'));
      try {
        const url = new URL(citation.url);
        if (!['https:', 'http:'].includes(url.protocol)) throw new Error('Unsupported citation URL');
        const link = document.createElement('a');
        link.textContent = citation.url;
        link.href = url.href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        li.appendChild(link);
      } catch (error) {
        li.appendChild(document.createTextNode(`${citation.url} (invalid citation link)`));
        appendLog(error.message, 'error');
      }
      const snippet = document.createElement('em');
      snippet.textContent = citation.snippet;
      li.append(document.createElement('br'), snippet);
      citationsList.appendChild(li);
    });
  }

  function applySnapshot(snapshot) {
    document.getElementById('primary-model-label').textContent = snapshot.primary_model;
    document.getElementById('escalation-model-label').textContent = snapshot.escalation_model;
    if (!submitting && snapshot.current_run_id !== currentRunId) {
      currentRunId = snapshot.current_run_id;
      lastSequence = 0;
      resetMatrix();
      if (!currentRunId) {
        stepperMode.textContent = 'STANDBY';
        verdictBadge.textContent = 'AWAITING RUN';
      }
    }
    (snapshot.events || []).forEach(handleProofLoopEvent);
    if (snapshot.last_report) renderReport(snapshot.last_report);
    if (snapshot.last_error) {
      verdictBadge.textContent = 'FAILED';
      verdictBadge.className = 'verdict-tag failed';
      setStepperPhase('FAILED');
    }
    if (!submitting) setRunning(snapshot.status === 'running' && !snapshot.last_verdict);
  }

  async function syncStatus() {
    try {
      const response = await fetch('/api/status');
      if (!response.ok) throw new Error(`Status request failed (${response.status})`);
      applySnapshot(await response.json());
    } catch (error) {
      appendLog(`Could not synchronize dashboard: ${error.message}`, 'error');
    }
  }

  function updateMatrixItem(id, passed) {
    const pill = document.getElementById(`status-${id}`);
    if (!pill) return;
    if (passed) {
      pill.textContent = 'PASSED';
      pill.className = 'matrix-status-pill passed';
    } else {
      pill.textContent = 'FAILED';
      pill.className = 'matrix-status-pill failed';
    }
  }

  // Connect SSE
  let evtSource = null;
  function connectSSE() {
    evtSource = new EventSource('/api/stream');

    evtSource.addEventListener('connected', () => {
      connectionStatus.classList.add('connected');
      connectionLabel.textContent = 'EventBus Connected (Live SSE)';
      appendLog('SSE stream established to ProofLoop EventBus.', 'success');
    });

    evtSource.addEventListener('proofloop', (e) => {
      try {
        const eventData = JSON.parse(e.data);
        handleProofLoopEvent(eventData);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
        appendLog(`Invalid ProofLoop event: ${err.message}`, 'error');
      }
    });
    evtSource.addEventListener('snapshot', (e) => {
      try {
        applySnapshot(JSON.parse(e.data));
      } catch (error) {
        appendLog(`Invalid dashboard snapshot: ${error.message}`, 'error');
      }
    });

    evtSource.onerror = () => {
      connectionStatus.classList.remove('connected');
      connectionLabel.textContent = 'Reconnecting to EventBus...';
    };
  }

  function handleProofLoopEvent(event) {
    if (event.sequence && event.sequence <= lastSequence) return;
    if (event.sequence) lastSequence = event.sequence;
    if (event.run_id && event.run_id !== currentRunId) {
      currentRunId = event.run_id;
      resetMatrix();
    }
    const { event_type, phase, payload } = event;

    if (event_type === 'PHASE_CHANGE' && payload && payload.phase) {
      setStepperPhase(payload.phase);
      appendLog(`Phase Transition -> ${payload.phase}`, 'phase');
      if (payload.escalated) {
        appendLog(`Escalation active: ${document.getElementById('escalation-model-label').textContent}`, 'guard');
      }
    } else if (event_type === 'RESEARCH_COMPLETE') {
      appendLog(`Tavily research completed: ${payload.citations?.length || 0} citations retrieved`, 'phase');
      renderCitations(payload.citations || []);
    } else if (event_type === 'PATCH_GENERATED' && payload.patch) {
      appendLog(`Patch synthesized with regression test.`, 'success');
      renderPatch(payload.patch);
    } else if (event_type === 'GIT_GUARD_VERIFIED') {
      appendLog('Git Guard Policy passed: Baseline tests & build config unmodified.', 'guard');
      updateMatrixItem('gitguard', true);
    } else if (event_type === 'GIT_GUARD_VIOLATION') {
      appendLog(`Git Guard Policy violation: ${payload.violations?.join(', ')}`, 'error');
      updateMatrixItem('gitguard', false);
    } else if (event_type === 'DOUBLE_VERIFICATION_COMPLETE') {
      appendLog(`Double-Verification check complete. Repro: ${!payload.baseline_passed}, Fix: ${payload.patched_passed}, Zero Regressions: ${payload.suite_passed}`,
        !payload.baseline_passed && payload.patched_passed && payload.suite_passed && payload.git_guard_passed ? 'success' : 'error');
      updateMatrixItem('repro', !payload.baseline_passed);
      updateMatrixItem('fix', payload.patched_passed);
      updateMatrixItem('regression', payload.suite_passed);
      updateMatrixItem('gitguard', payload.git_guard_passed);
    } else if (event_type === 'RUN_COMPLETE') {
      appendLog(`ProofLoop run finished. Final Verdict: ${payload.verdict}`, payload.verdict === 'VERIFIED' ? 'success' : 'error');
      verdictBadge.textContent = payload.verdict;
      verdictBadge.className = `verdict-tag ${payload.verdict.toLowerCase()}`;
      if (payload.report) renderReport(payload.report);
      setStepperPhase('COMPLETED');
      setRunning(false);
    } else if (event_type === 'RUN_FAILED') {
      appendLog(`ProofLoop run failed: ${payload.error}`, 'error');
      verdictBadge.textContent = 'FAILED';
      verdictBadge.className = 'verdict-tag failed';
      setStepperPhase('FAILED');
      setRunning(false);
    } else if (event_type === 'RUN_STARTED') {
      setRunning(true);
    } else {
      appendLog(`[${event_type}] ${JSON.stringify(payload)}`, 'system');
    }
  }

  // Handle Run Trigger
  runForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (btnRunLoop.disabled) return;
    submitting = true;
    setRunning(true);
    resetMatrix();
    setStepperPhase('INTAKE');

    const payload = {
      title: issueTitleInput.value,
      description: issueTitleInput.value,
      traceback: tracebackInput.value,
      target_package: targetPkgInput.value,
      package_version: pkgVersionInput.value,
      case_id: selectedCase,
      mode: "demo"
    };

    try {
      appendLog(`Submitting ProofLoop task: "${payload.title}"`, 'phase');
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.headers.get('content-type')?.includes('application/json')) {
        throw new Error(`Engine returned HTTP ${res.status}: ${await res.text()}`);
      }
      const data = await res.json();
      if (!res.ok) {
        const detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        throw new Error(detail || `HTTP ${res.status}`);
      }
      if (!data.run_id) throw new Error('Engine response is missing a run ID');
      appendLog(`Task accepted by engine. Run ID: ${data.run_id}`, 'system');
    } catch (err) {
      appendLog(`Failed to trigger ProofLoop: ${err.message}`, 'error');
      verdictBadge.textContent = 'FAILED';
      verdictBadge.className = 'verdict-tag failed';
      setStepperPhase('FAILED');
      setRunning(false);
    } finally {
      submitting = false;
    }
  });

  // Start SSE connection
  connectSSE();
  syncStatus();
  const statusTimer = setInterval(syncStatus, 2000);
  window.addEventListener('pagehide', () => {
    clearInterval(statusTimer);
    evtSource.close();
  });
});
