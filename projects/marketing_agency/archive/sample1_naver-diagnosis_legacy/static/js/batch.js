// 배치 진단 기능

let batchId = null;
let pollingInterval = null;
let selectedFile = null;
let selectedFilePath = null;

// 파일 선택 핸들러
function handleFileSelect(event) {
    selectedFile = event.target.files[0];

    if (selectedFile) {
        document.getElementById('fileName').textContent = selectedFile.name;
        document.getElementById('fileSize').textContent = `크기: ${(selectedFile.size / 1024).toFixed(2)} KB`;
        document.getElementById('fileInfo').classList.remove('hidden');
        document.getElementById('startBatchBtn').disabled = false;
    }
}

// 파일 경로 입력 감지
document.addEventListener('DOMContentLoaded', () => {
    const filePathInput = document.getElementById('filePath');
    if (filePathInput) {
        filePathInput.addEventListener('input', (e) => {
            selectedFilePath = e.target.value.trim();
            if (selectedFilePath) {
                document.getElementById('startBatchBtn').disabled = false;
            } else if (!selectedFile) {
                document.getElementById('startBatchBtn').disabled = true;
            }
        });
    }
});

// 배치 진단 시작
async function startBatch() {
    const startBtn = document.getElementById('startBatchBtn');
    startBtn.disabled = true;
    startBtn.textContent = '시작 중...';

    try {
        let response;

        if (selectedFile) {
            // 파일 업로드 방식
            const formData = new FormData();
            formData.append('file', selectedFile);

            response = await fetch('/batch/upload', {
                method: 'POST',
                body: formData
            });
        } else if (selectedFilePath) {
            // 파일 경로 방식
            response = await fetch('/batch/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ file_path: selectedFilePath })
            });
        } else {
            alert('파일을 선택하거나 경로를 입력해주세요.');
            startBtn.disabled = false;
            startBtn.textContent = '배치 진단 시작';
            return;
        }

        if (response.ok) {
            const data = await response.json();
            batchId = data.batch_id;

            // UI 전환
            document.getElementById('progressSection').classList.remove('hidden');
            startBtn.textContent = '진행 중...';

            // 로그 추가
            addLog(`[시작] 배치 ID: ${batchId}`);
            addLog(`[정보] 총 ${data.total}개 업체 진단 시작`);

            // 진행 상태 폴링 시작
            startPolling();
        } else {
            const error = await response.json();
            alert(`배치 시작 실패: ${error.detail || '알 수 없는 오류'}`);
            startBtn.disabled = false;
            startBtn.textContent = '배치 진단 시작';
        }
    } catch (error) {
        console.error('Batch start error:', error);
        alert('배치 진단 시작 중 오류가 발생했습니다.');
        startBtn.disabled = false;
        startBtn.textContent = '배치 진단 시작';
    }
}

// 진행 상태 폴링
function startPolling() {
    // 즉시 한 번 실행
    updateProgress();

    // 3초마다 상태 확인
    pollingInterval = setInterval(updateProgress, 3000);
}

// 진행 상태 업데이트
async function updateProgress() {
    if (!batchId) return;

    try {
        const response = await fetch(`/batch/status/${batchId}`);

        if (response.ok) {
            const data = await response.json();

            // 통계 업데이트
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-success').textContent = data.success;
            document.getElementById('stat-fail').textContent = data.failed;

            // 진행률 계산
            const percent = Math.round((data.processed / data.total) * 100);
            document.getElementById('progressPercent').textContent = `${percent}%`;
            document.getElementById('progressCount').textContent = `${data.processed} / ${data.total}`;
            document.getElementById('progressBar').style.width = `${percent}%`;

            // 상태 메시지
            if (data.status === 'completed') {
                document.getElementById('progressText').textContent = '완료';
                addLog(`[완료] 전체 진단이 완료되었습니다.`);
                showComplete(data);
                stopPolling();
            } else if (data.status === 'failed') {
                document.getElementById('progressText').textContent = '실패';
                addLog(`[오류] 배치 진단이 실패했습니다.`, 'error');
                stopPolling();
            } else {
                document.getElementById('progressText').textContent = '진행 중...';
            }

            // 최근 처리된 업체 로그
            if (data.last_processed) {
                addLog(`[진행] ${data.last_processed.business_name} - ${data.last_processed.status}`);
            }
        }
    } catch (error) {
        console.error('Progress update error:', error);
    }
}

// 폴링 중단
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// 배치 중단
async function stopBatch() {
    if (!batchId) return;

    if (!confirm('정말로 진단을 중단하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/batch/cancel/${batchId}`, {
            method: 'POST'
        });

        if (response.ok) {
            addLog(`[중단] 사용자가 배치를 중단했습니다.`, 'warning');
            stopPolling();
            document.getElementById('progressText').textContent = '중단됨';
        }
    } catch (error) {
        console.error('Stop batch error:', error);
        alert('배치 중단 중 오류가 발생했습니다.');
    }
}

// 완료 화면 표시
function showComplete(data) {
    document.getElementById('progressSection').classList.add('hidden');
    document.getElementById('completeSection').classList.remove('hidden');

    // 최종 통계
    document.getElementById('final-total').textContent = data.total;
    document.getElementById('final-success').textContent = data.success;
    document.getElementById('final-fail').textContent = data.failed;
    document.getElementById('final-priority1').textContent = data.priority_1_count || 0;

    // 완료 메시지
    const successRate = Math.round((data.success / data.total) * 100);
    document.getElementById('completeMessage').textContent =
        `${data.total}개 업체 중 ${data.success}개 성공 (성공률 ${successRate}%)`;
}

// 로그 추가
function addLog(message, level = 'info') {
    const logContainer = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');

    let color = 'text-gray-300';
    if (level === 'error') color = 'text-red-400';
    else if (level === 'warning') color = 'text-yellow-400';
    else if (level === 'success') color = 'text-green-400';

    logEntry.className = color;
    logEntry.textContent = `[${timestamp}] ${message}`;

    logContainer.appendChild(logEntry);

    // 자동 스크롤
    logContainer.scrollTop = logContainer.scrollHeight;

    // 최대 100개 로그만 유지
    while (logContainer.children.length > 100) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

// 리셋
function resetBatch() {
    // 상태 초기화
    batchId = null;
    selectedFile = null;
    selectedFilePath = null;
    stopPolling();

    // UI 초기화
    document.getElementById('excelFile').value = '';
    document.getElementById('filePath').value = '';
    document.getElementById('fileInfo').classList.add('hidden');
    document.getElementById('progressSection').classList.add('hidden');
    document.getElementById('completeSection').classList.add('hidden');
    document.getElementById('startBatchBtn').disabled = true;
    document.getElementById('startBatchBtn').textContent = '배치 진단 시작';

    // 로그 초기화
    document.getElementById('logContainer').innerHTML =
        '<div class="text-green-400">[시작] 배치 진단을 준비 중입니다...</div>';

    // 통계 초기화
    document.getElementById('stat-total').textContent = '0';
    document.getElementById('stat-success').textContent = '0';
    document.getElementById('stat-fail').textContent = '0';
    document.getElementById('progressBar').style.width = '0%';
}
