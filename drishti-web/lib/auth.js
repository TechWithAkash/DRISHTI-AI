export function createMockJWT(payload) {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const body = btoa(JSON.stringify({ ...payload, exp: Date.now() + 86400000 }));
    const signature = btoa('mock-signature');
    return `${header}.${body}.${signature}`;
}

export function parseMockJWT(token) {
    try {
        const body = token.split('.')[1];
        const parsed = JSON.parse(atob(body));
        if (parsed.exp < Date.now()) return null;
        return parsed;
    } catch (e) {
        return null;
    }
}
