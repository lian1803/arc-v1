// Result page interactions

function downloadPPT(historyId, callerBtn) {
    // result 페이지 전용 버튼 요소 (없을 수 있음 — history 페이지에서도 호출됨)
    const btn = document.getElementById('downloadPptBtn');
    const btnText = document.getElementById('downloadBtnText');
    const btnSpinner = document.getElementById('downloadBtnSpinner');

    if (btn) {
        // result 페이지: 전용 버튼 UI 사용
        if (btn.disabled) return;
        btn.disabled = true;
        if (btnText) btnText.textContent = 'PPT 생성 중...';
        if (btnSpinner) btnSpinner.classList.remove('hidden');
    } else if (callerBtn) {
        // history 페이지: 전달받은 버튼에 로딩 표시
        if (callerBtn.disabled) return;
        callerBtn.disabled = true;
        callerBtn._origText = callerBtn.textContent;
        callerBtn.textContent = '생성 중...';
    }

    // Create download link
    const downloadUrl = `/ppt/generate/${historyId}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `네이버_플레이스_진단_${historyId}.pptx`;

    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Reset button after delay (assume download starts)
    setTimeout(() => {
        if (btn) {
            btn.disabled = false;
            if (btnText) btnText.textContent = 'PPT 제안서 다운로드';
            if (btnSpinner) btnSpinner.classList.add('hidden');
        } else if (callerBtn) {
            callerBtn.disabled = false;
            callerBtn.textContent = callerBtn._origText || 'PPT 다운';
        }
    }, 2000);
}

function downloadPDF(historyId) {
    const btn = document.getElementById('downloadPdfBtn');
    const btnText = document.getElementById('downloadPdfBtnText');
    const btnSpinner = document.getElementById('downloadPdfBtnSpinner');

    if (btn && btn.disabled) return;
    if (btn) {
        btn.disabled = true;
        if (btnText) btnText.textContent = 'PDF 생성 중...';
        if (btnSpinner) btnSpinner.classList.remove('hidden');
    }

    fetch(`/ppt/generate-pdf/${historyId}`)
        .then(res => res.json())
        .then(data => {
            if (data.download_url) {
                const link = document.createElement('a');
                link.href = data.download_url;
                link.download = `네이버_플레이스_진단_${historyId}.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                alert('PDF 생성 실패: ' + (data.detail || '알 수 없는 오류'));
            }
        })
        .catch(err => alert('PDF 생성 실패: ' + err))
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                if (btnText) btnText.textContent = 'PDF 제안서 다운로드';
                if (btnSpinner) btnSpinner.classList.add('hidden');
            }
        });
}

// Optional: Add smooth scroll to improvement points on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add any additional page initialization here
    console.log('Result page loaded successfully');

    // URL 해시에 메시지 앵커가 있으면 스크롤
    if (window.location.hash === '#messages') {
        setTimeout(() => {
            const messagesSection = document.querySelector('.message-tabs');
            if (messagesSection) {
                messagesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 300);
    }
});
