/**
 * 식품 스케줄러 공용 스크립트
 */

// API 기본 URL
const API_BASE_URL = '';

// 토큰 관리 함수
const TokenManager = {
    // 액세스 토큰 가져오기
    getAccessToken: function() {
        const localToken = localStorage.getItem('access_token');
        console.log('getAccessToken 호출됨 - 로컬 스토리지에서 토큰:', localToken ? '찾음' : '없음');
        return localToken;
    },
    
    // 리프레시 토큰 가져오기
    getRefreshToken: function() {
        return localStorage.getItem('refresh_token');
    },
    
    // 쿠키에서 토큰 가져오기
    getTokenFromCookie: function(name) {
        const value = `; ${document.cookie}`;
        console.log(`getTokenFromCookie(${name}) 호출됨 - 전체 쿠키:`, document.cookie);
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            const token = parts.pop().split(';').shift();
            console.log(`- 쿠키에서 ${name} 토큰 발견:`, token ? '있음' : '없음');
            return token;
        }
        console.log(`- 쿠키에서 ${name} 토큰을 찾을 수 없음`);
        return null;
    },
    
    // 토큰 저장
    setTokens: function(access_token, refresh_token) {
        localStorage.setItem('access_token', access_token);
        if (refresh_token) {
            localStorage.setItem('refresh_token', refresh_token);
        }
    },
    
    // 토큰 삭제 (로그아웃)
    clearTokens: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // 쿠키에서도 토큰 삭제
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; HttpOnly; Secure; SameSite=Lax;';
    },
    
    // 토큰 유효 여부 확인
    isLoggedIn: function() {
        const accessToken = this.getAccessToken();
        const cookieToken = this.getTokenFromCookie('access_token');
        console.log('TokenManager.isLoggedIn 호출됨');
        console.log('- 로컬 스토리지 토큰:', accessToken ? '있음' : '없음');
        console.log('- 쿠키 토큰:', cookieToken ? '있음' : '없음');
        
        // 디버깅을 위해 항상 로그인된 것으로 간주
        const isLoggedIn = true; // !!(accessToken || cookieToken);
        console.log('- 로그인 상태:', isLoggedIn ? '로그인됨' : '로그인 안됨');
        return isLoggedIn;
    }
};

// API 호출 헬퍼
const ApiClient = {
    // GET 요청
    get: async function(endpoint, requireAuth = true) {
        const headers = this._getHeaders(requireAuth);
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, { 
                method: 'GET', 
                headers 
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },
    
    // POST 요청
    post: async function(endpoint, data, requireAuth = true) {
        const headers = this._getHeaders(requireAuth);
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers,
                body: JSON.stringify(data)
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },
    
    // PUT 요청
    put: async function(endpoint, data, requireAuth = true) {
        const headers = this._getHeaders(requireAuth);
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'PUT',
                headers,
                body: JSON.stringify(data)
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API PUT Error:', error);
            throw error;
        }
    },
    
    // DELETE 요청
    delete: async function(endpoint, requireAuth = true) {
        const headers = this._getHeaders(requireAuth);
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, { 
                method: 'DELETE', 
                headers 
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    },
    
    // 헤더 생성
    _getHeaders: function(requireAuth) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (requireAuth) {
            const token = TokenManager.getAccessToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        
        return headers;
    },
    
    // 응답 처리
    _handleResponse: async function(response) {
        // 액세스 토큰 만료 시 갱신 시도
        if (response.status === 401 && TokenManager.getRefreshToken()) {
            try {
                await this._refresh_token();
                // 새 토큰으로 원래 요청 다시 시도
                const newHeaders = this._getHeaders(true);
                const retryResponse = await fetch(response.url, {
                    method: response.method,
                    headers: newHeaders,
                    body: response.body
                });
                return this._parseResponse(retryResponse);
            } catch (error) {
                // 토큰 갱신 실패 시 로그인 페이지로 이동 (디버깅을 위해 비활성화)
                TokenManager.clearTokens();
                console.error('토큰 갱신 실패 (리다이렉트 비활성화됨):', error);
                // window.location.href = '/login';
                throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
            }
        }
        
        return this._parseResponse(response);
    },
    
    // 응답 파싱
    _parseResponse: async function(response) {
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            const error = new Error(data.detail || '요청 처리 중 오류가 발생했습니다.');
            error.status = response.status;
            error.data = data;
            throw error;
        }
        
        return data;
    },
    
    // 토큰 갱신
    _refresh_token: async function() {
        const refresh_token = TokenManager.getRefreshToken();
        if (!refresh_token) {
            throw new Error('리프레시 토큰이 없습니다.');
        }
        
        const response = await fetch(`${API_BASE_URL}/user/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refresh_token })
        });
        
        if (!response.ok) {
            throw new Error('토큰 갱신에 실패했습니다.');
        }
        
        const data = await response.json();
        TokenManager.setTokens(data.access_token, data.refresh_token);
        return data;
    }
};

// 사용자 관련 함수
const UserService = {
    // 로그인
    login: async function(email, password) {
        const data = await ApiClient.post('/user/login', { email, password }, false);
        TokenManager.setTokens(data.access_token, data.refresh_token);
        return data;
    },
    
    // 회원가입
    register: async function(userData) {
        return ApiClient.post('/user/register', userData, false);
    },
    
    // OAuth 회원가입
    oauthRegister: async function(oauthData) {
        return ApiClient.post('/user/oauth/register', oauthData, false);
    },
    
    // 이메일 인증 요청
    requestVerification: async function(email) {
        return ApiClient.post('/user/verify/email', { email }, false);
    },
    
    // 이메일 인증 확인
    confirmVerification: async function(email, code) {
        return ApiClient.post('/user/verify/confirm', { email, code }, false);
    },
    
    // 사용자 정보 조회
    getUserInfo: async function() {
        return ApiClient.get('/user/me');
    },
    
    // 로그아웃
    logout: async function() {
        await ApiClient.post('/user/logout', {});
        TokenManager.clearTokens();
    }
};

// UI 헬퍼 함수
const UiHelper = {
    // 경고 메시지 표시
    showAlert: function(elementId, message, type = 'danger', duration = 5000) {
        const alertElement = document.getElementById(elementId);
        if (!alertElement) return;
        
        alertElement.textContent = message;
        alertElement.className = `alert alert-${type}`;
        alertElement.classList.remove('d-none');
        
        if (duration) {
            setTimeout(() => {
                alertElement.classList.add('d-none');
            }, duration);
        }
    },
    
    // 로딩 상태 표시
    showLoading: function(button, isLoading) {
        if (!button) return;
        
        if (isLoading) {
            button.setAttribute('disabled', 'disabled');
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span class="ms-1">처리중...</span>
            `;
        } else {
            button.removeAttribute('disabled');
            button.innerHTML = button.getAttribute('data-original-text') || button.innerHTML;
        }
    },
    
    // 페이지 초기화 시 로그인 상태 확인
    checkLoginStatus: function() {
        if (!TokenManager.isLoggedIn() && !window.location.pathname.includes('login') && !window.location.pathname.includes('register')) {
            console.log('토큰이 없습니다. 로그인이 필요합니다. (리디렉션 비활성화)');
            // window.location.href = '/login';
        }
    }
};

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    // 자동 리다이렉트 비활성화 - 디버깅 용도
    console.log("자동 로그인 체크 비활성화됨 (디버깅 모드)");
    console.log("현재 경로:", window.location.pathname);
    console.log("토큰 상태:", TokenManager.isLoggedIn() ? "로그인됨" : "로그인 안됨");
    
    // 리다이렉트 비활성화
    // if (!window.location.pathname.includes('login') && !window.location.pathname.includes('register') && !window.location.pathname.includes('index')) {
    //     UiHelper.checkLoginStatus();
    // }
}); 