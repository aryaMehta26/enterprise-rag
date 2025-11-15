const e = React.createElement;

// Determine API base URL: same-origin by default, override via ?api= or window.API_BASE_URL
const API_BASE = (() => {
  try {
    const qp = new URLSearchParams(window.location.search);
    const fromQuery = qp.get('api');
    if (fromQuery) return String(fromQuery).replace(/\/$/, '');
    if (window.API_BASE_URL) return String(window.API_BASE_URL).replace(/\/$/, '');
  } catch (_) {}
  return '';
})();

function App() {
  const [token, setToken] = React.useState(null);
  const [username, setUsername] = React.useState('admin@example.com');
  const [password, setPassword] = React.useState('password');
  const [question, setQuestion] = React.useState('');
  const [source, setSource] = React.useState('all');
  const [answer, setAnswer] = React.useState('');
  const [sources, setSources] = React.useState([]);
  const [error, setError] = React.useState('');

  const login = async () => {
    setError('');
    try {
      const body = new URLSearchParams();
      body.set('username', username);
      body.set('password', password);
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setToken(data.access_token);
    } catch (err) {
      setError(String(err));
    }
  };

  const ask = async () => {
    setError('');
    setAnswer('');
    setSources([]);
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question, source })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAnswer(data.result);
      setSources(data.sources || []);
    } catch (err) {
      setError(String(err));
    }
  };

  if (!token) {
    return e('div', { className: 'container' }, [
      e('h1', { key: 'h' }, 'Enterprise RAG'),
      e('div', { key: 'u' }, [
        e('input', { placeholder: 'email', value: username, onChange: e=>setUsername(e.target.value)}),
        e('input', { placeholder: 'password', type:'password', value: password, onChange: e=>setPassword(e.target.value)}),
        e('button', { onClick: login }, 'Login')
      ]),
      e('div', { key: 'api', style: { marginTop: 8, opacity: 0.85 } }, `API: ${API_BASE || '(same origin)'}`),
      error && e('pre', { key: 'err', className: 'error' }, error)
    ]);
  }

  return e('div', { className: 'container' }, [
    e('h1', { key: 'h' }, 'Ask a question'),
    e('div', { key: 'q' }, [
      e('input', { placeholder: 'Your question', value: question, onChange: e=>setQuestion(e.target.value)}),
      e('select', { value: source, onChange: e=>setSource(e.target.value)}, [
        e('option', { value:'all' }, 'all'),
        e('option', { value:'PDF' }, 'PDF'),
        e('option', { value:'Wikipedia' }, 'Wikipedia')
      ]),
      e('button', { onClick: ask }, 'Ask')
    ]),
    answer && e('div', { key: 'a' }, [e('h3', null, 'Answer'), e('pre', null, answer)]),
    sources.length>0 && e('div', { key: 's' }, [e('h3', null, 'Sources'), e('ul', null, sources.map((s,i)=>e('li',{key:i}, s))) ]),
    e('div', { key: 'api', style: { marginTop: 8, opacity: 0.85 } }, `API: ${API_BASE || '(same origin)'}`),
    error && e('pre', { key: 'err', className: 'error' }, error)
  ]);
}

ReactDOM.createRoot(document.getElementById('root')).render(e(App));
