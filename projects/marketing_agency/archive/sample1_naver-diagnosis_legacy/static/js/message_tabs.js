// 영업 메시지 탭 전환 및 복사 기능

// 메시지 탭 전환
function switchMessageTab(tabNumber) {
    // 모든 탭 비활성화
    document.querySelectorAll('.message-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // 선택된 탭 활성화
    const selectedTab = document.querySelector(`.message-tab[data-tab="${tabNumber}"]`);
    const selectedPanel = document.getElementById(`tab-panel-${tabNumber}`);

    if (selectedTab) selectedTab.classList.add('active');
    if (selectedPanel) selectedPanel.classList.add('active');
}

// 1차 메시지 버전 전환
function switchFirstVersion(versionNumber) {
    document.querySelectorAll('.first-version-content').forEach(content => {
        content.style.display = 'none';
    });
    const selectedContent = document.getElementById(`first-message-${versionNumber}`);
    if (selectedContent) {
        selectedContent.style.display = 'block';
    }
}

// 4차 메시지 버전 전환
function switchFourthVersion(versionNumber) {
    document.querySelectorAll('.fourth-version-content').forEach(content => {
        content.style.display = 'none';
    });
    const selectedContent = document.getElementById(`fourth-message-${versionNumber}`);
    if (selectedContent) {
        selectedContent.style.display = 'block';
    }
}

// 클립보드 복사 (폴백 포함)
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // 폴백: execCommand (deprecated이지만 HTTP 환경 대응)
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        return success;
    }
}

// 메시지 복사 버튼 핸들러 (개선된 피드백)
async function copyMessage(elementId, button) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Element with id ${elementId} not found`);
        return;
    }

    const text = element.textContent || element.innerText;
    const success = await copyToClipboard(text);

    if (success) {
        // 원본 상태 저장
        const originalText = button.textContent;
        const originalClass = button.className;

        // 성공 상태로 변경
        button.textContent = '✓ 복사됨!';
        button.className = originalClass + ' bg-green-600 hover:bg-green-700 border-green-600';
        button.disabled = true;

        // 토스트 알림 표시 (선택사항: 더 시각적 피드백)
        showCopyToast('메시지가 클립보드에 복사되었습니다!');

        // 2초 후 원래대로 복원
        setTimeout(() => {
            button.textContent = originalText;
            button.className = originalClass;
            button.disabled = false;
        }, 2000);
    } else {
        alert('복사에 실패했습니다. 다시 시도해주세요.');
    }
}

// 토스트 알림 (복사 완료 시 화면 우측 하단에 표시)
function showCopyToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50 animate-fade-in-up';
    toast.innerHTML = `
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);

    // 2초 후 제거
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// 우선순위 드롭다운 토글
function togglePriorityDropdown() {
    const dropdown = document.getElementById('priorityDropdown');
    if (dropdown) {
        dropdown.classList.toggle('open');
    }

    // 외부 클릭 시 닫기
    document.addEventListener('click', function closeDropdown(e) {
        const badge = document.getElementById('priorityBadge');
        if (!badge.contains(e.target)) {
            dropdown.classList.remove('open');
            document.removeEventListener('click', closeDropdown);
        }
    });
}

// 우선순위 변경
async function changePriority(priorityValue, priorityLabel) {
    const dropdown = document.getElementById('priorityDropdown');
    const badge = document.getElementById('priorityBadge');

    // 현재 페이지 URL에서 history_id 추출
    const pathParts = window.location.pathname.split('/');
    const historyId = pathParts[pathParts.length - 1];

    try {
        const response = await fetch(`/api/businesses/${historyId}/priority`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ priority: priorityLabel })
        });

        if (response.ok) {
            // UI 업데이트
            badge.className = `priority-badge priority-${priorityValue}`;
            badge.innerHTML = `${priorityLabel} <span style="font-size: 0.7em;">▼</span>`;
            dropdown.classList.remove('open');
        } else {
            alert('우선순위 변경에 실패했습니다.');
        }
    } catch (error) {
        console.error('Priority update error:', error);
        alert('우선순위 변경 중 오류가 발생했습니다.');
    }
}

// 페이지 로드 시 점수 바 애니메이션
window.addEventListener('load', () => {
    document.querySelectorAll('.score-bar').forEach(bar => {
        const target = bar.getAttribute('data-target');
        if (target) {
            setTimeout(() => {
                bar.style.width = `${target}%`;
            }, 100);
        }
    });
});
