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
  const issueTitleInput = document.getElementById('issue-title');
  const targetPkgInput = document.getElementById('target-package');
  const pkgVersionInput = document.getElementById('package-version');
  const tracebackInput = document.getElementById('issue-traceback');

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
    }
  };

  btnPresetPydantic.addEventListener('click', () => {
    btnPresetPydantic.classList.add('active');
    btnPresetRequests.classList.remove('active');
    issueTitleInput.value = PRESETS.pydantic.title;
    targetPkgInput.value = PRESETS.pydantic.package;
    pkgVersionInput.value = PRESETS.pydantic.version;
    tracebackInput.value = PRESETS.pydantic.traceback;
  });

  btnPresetRequests.addEventListener('click', () => {
    btnPresetRequests.classList.add('active');
    btnPresetPydantic.classList.remove('active');
    issueTitleInput.value = PRESETS.requests.title;
    targetPkgInput.value = PRESETS.requests.package;
    pkgVersionInput.value = PRESETS.requests.version;
    tracebackInput.value = PRESETS.requests.traceback;
  });

  function appendLog(text, type = 'system') {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    line.textContent = `[${timestamp}] ${text}`;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }

  btnClearLogs.addEventListener('click', () => {
    terminalLogs.innerHTML = '';
    appendLog('Log cleared by user.', 'system');
  });

  function setStepperPhase(currentPhase) {
    let passedCurrent = false;
    PIPELINE_PHASES.forEach(phase => {
      const node = document.getElementById(`step-${phase}`);
      if (!node) return;

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
    });
    stepperMode.textContent = currentPhase;
  }

  function resetMatrix() {
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
      }
    });

    evtSource.onerror = () => {
      connectionStatus.classList.remove('connected');
      connectionLabel.textContent = 'Reconnecting to EventBus...';
    };
  }

  function handleProofLoopEvent(event) {
    const { event_type, phase, payload } = event;

    if (event_type === 'PHASE_CHANGE' && payload && payload.phase) {
      setStepperPhase(payload.phase);
      appendLog(`Phase Transition -> ${payload.phase}`, 'phase');
      if (payload.escalated) {
        appendLog(`Escalation active: using NVIDIA Nemotron 550b Ultra`, 'guard');
      }
    } else if (event_type === 'RESEARCH_COMPLETE') {
      appendLog(`Tavily research completed: ${payload.citations?.length || 0} citations retrieved`, 'phase');
      if (payload.citations && payload.citations.length > 0) {
        citationsList.innerHTML = '';
        payload.citations.forEach(c => {
          const li = document.createElement('li');
          li.innerHTML = `<strong>${c.title}</strong><br><a href="${c.url}" target="_blank">${c.url}</a><br><em>${c.snippet}</em>`;
          citationsList.appendChild(li);
        });
      }
    } else if (event_type === 'PATCH_GENERATED' && payload.patch) {
      appendLog(`Patch synthesized with regression test.`, 'success');
      const patch = payload.patch;
      if (patch.diffs && patch.diffs.length > 0) {
        patchFileLabel.textContent = patch.diffs[0].file_path;
        diffContent.textContent = `--- ${patch.diffs[0].file_path} (before)\n+++ ${patch.diffs[0].file_path} (after)\n` +
          `- ${patch.diffs[0].old_content}\n+ ${patch.diffs[0].new_content}\n\n` +
          `# Isolated Regression Test: ${patch.regression_test_file}\n` +
          `${patch.regression_test_code}`;
      }
    } else if (event_type === 'GIT_GUARD_VERIFIED') {
      appendLog('Git Guard Policy passed: Baseline tests & build config unmodified.', 'guard');
      updateMatrixItem('gitguard', true);
    } else if (event_type === 'GIT_GUARD_VIOLATION') {
      appendLog(`Git Guard Policy violation: ${payload.violations?.join(', ')}`, 'error');
      updateMatrixItem('gitguard', false);
    } else if (event_type === 'DOUBLE_VERIFICATION_COMPLETE') {
      appendLog(`Double-Verification check complete. Repro: ${!payload.baseline_passed}, Fix: ${payload.patched_passed}, Zero Regressions: ${payload.suite_passed}`, 'success');
      updateMatrixItem('repro', !payload.baseline_passed);
      updateMatrixItem('fix', payload.patched_passed);
      updateMatrixItem('regression', payload.suite_passed);
      updateMatrixItem('gitguard', payload.git_guard_passed);
    } else if (event_type === 'RUN_COMPLETE') {
      appendLog(`ProofLoop run finished. Final Verdict: ${payload.verdict}`, payload.verdict === 'VERIFIED' ? 'success' : 'error');
      verdictBadge.textContent = payload.verdict;
      verdictBadge.className = `verdict-tag ${payload.verdict.toLowerCase()}`;
      btnRunLoop.disabled = false;
      btnRunLoop.innerHTML = '<span class="btn-icon">⚡</span> Run ProofLoop';
    } else {
      appendLog(`[${event_type}] ${JSON.stringify(payload)}`, 'system');
    }
  }

  // Handle Run Trigger
  runForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    btnRunLoop.disabled = true;
    btnRunLoop.innerHTML = '<span class="btn-icon">⏳</span> Running...';
    resetMatrix();
    setStepperPhase('INTAKE');

    const payload = {
      title: issueTitleInput.value,
      description: issueTitleInput.value,
      traceback: tracebackInput.value,
      target_package: targetPkgInput.value,
      package_version: pkgVersionInput.value,
      mode: "demo"
    };

    try {
      appendLog(`Submitting ProofLoop task: "${payload.title}"`, 'phase');
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      appendLog(`Task accepted by engine. Run ID: ${data.run_id}`, 'system');
    } catch (err) {
      appendLog(`Failed to trigger ProofLoop: ${err.message}`, 'error');
      btnRunLoop.disabled = false;
      btnRunLoop.innerHTML = '<span class="btn-icon">⚡</span> Run ProofLoop';
    }
  });

  // Start SSE connection
  connectSSE();
});
