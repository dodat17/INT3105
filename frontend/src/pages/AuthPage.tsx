import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';

type AuthPageProps = {
  mode: 'login' | 'register';
};

type LocationState = {
  from?: string;
  email?: string;
  registered?: boolean;
};

export function AuthPage({ mode }: AuthPageProps) {
  const { authReady, login, register, user } = useOutletContext<AppContext>();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | null;
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (authReady && user) return <Navigate replace to={user.role === 'ADMIN' ? '/admin' : '/'} />;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get('email') ?? '').trim();
    const password = String(form.get('password') ?? '');
    setError('');
    setSubmitting(true);
    try {
      if (mode === 'register') {
        await register({ email, password, fullName: String(form.get('fullName') ?? '').trim() });
        navigate('/login', { replace: true, state: { email, registered: true } });
      } else {
        const currentUser = await login({ email, password });
        const destination = currentUser.role === 'ADMIN' ? '/admin' : state?.from ?? '/';
        navigate(destination, { replace: true });
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Không thể hoàn tất yêu cầu.');
    } finally {
      setSubmitting(false);
    }
  };

  const isRegister = mode === 'register';
  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <p className="section-index">TÀI KHOẢN</p>
        <h1>{isRegister ? 'Đăng ký' : 'Đăng nhập'}</h1>
        {!isRegister && state?.registered && <p className="form-notice success" role="status">Đăng ký thành công. Hãy đăng nhập để tiếp tục.</p>}
        {isRegister && <label>Họ và tên<input autoComplete="name" name="fullName" required /></label>}
        <label>Email<input autoComplete="email" defaultValue={state?.email} name="email" type="email" required /></label>
        <label>Mật khẩu<input autoComplete={isRegister ? 'new-password' : 'current-password'} minLength={8} name="password" type="password" required /></label>
        {error && <p className="form-notice error" role="alert">{error}</p>}
        <button className="button button-accent full-width" disabled={submitting} type="submit">
          {submitting ? 'Đang xử lý...' : isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}
        </button>
        <p className="auth-switch">
          {isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản?'}{' '}
          <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'Đăng nhập' : 'Đăng ký'}</Link>
        </p>
      </form>
    </section>
  );
}
