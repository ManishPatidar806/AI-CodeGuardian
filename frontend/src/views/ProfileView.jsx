import React, { useState } from 'react';
import { 
  User, 
  Mail, 
  Phone, 
  Key, 
  Shield, 
  Save, 
  CheckCircle2, 
  Lock, 
  Send
} from 'lucide-react';
import { updateUserProfile, changeAdminPasswordOTP } from '../services/api';

export function ProfileView({ currentUser, onUpdateUser }) {
  const isAdmin = currentUser?.role === 'ADMIN';

  // Profile Edit State for Admin
  const [name, setName] = useState(currentUser?.name || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [mobile, setMobile] = useState(currentUser?.mobile || '');

  // OTP Password Change State for Admin
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  const [profileSuccess, setProfileSuccess] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!isAdmin) return;

    const res = await updateUserProfile(currentUser.id, { name, email, mobile });
    if (res.success) {
      setProfileSuccess(true);
      onUpdateUser({ ...currentUser, name, email, mobile });
      setTimeout(() => setProfileSuccess(false), 3000);
    }
  };

  const handleSendOTP = () => {
    if (!mobile && !email) {
      setErrorMsg('Please save your Email or Mobile Number first to receive OTP.');
      return;
    }
    setOtpSent(true);
    setErrorMsg('');
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!otp || !newPassword) {
      setErrorMsg('Please enter both OTP code and new password.');
      return;
    }

    const res = await changeAdminPasswordOTP({ otp, new_password: newPassword });
    if (res.success) {
      setPasswordSuccess(true);
      setOtp('');
      setNewPassword('');
      setOtpSent(false);
      setTimeout(() => setPasswordSuccess(false), 3000);
    } else {
      setErrorMsg(res.error || 'Invalid OTP code.');
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              User Profile & Security
            </h2>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              isAdmin ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}>
              {currentUser?.role || 'EMPLOYEE'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {isAdmin 
              ? 'Update your admin contact information and change your password via Mobile/Email OTP.' 
              : 'View your account profile details and assigned role.'}
          </p>
        </div>

        {profileSuccess && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Profile Saved
          </span>
        )}
      </div>

      {/* Admin Profile Details Form */}
      {isAdmin ? (
        <div className="space-y-6">
          {/* Section 1: Admin Profile Details */}
          <form onSubmit={handleSaveProfile} className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
              <User className="w-4 h-4 text-slate-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Admin Details
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Primary Admin"
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@company.com"
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Mobile Number (For Password Reset OTP)
                </label>
                <input
                  type="text"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  placeholder="+1234567890"
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Username (Fixed)
                </label>
                <input
                  type="text"
                  value={currentUser?.username || 'admin'}
                  disabled
                  className="w-full px-3 py-1.5 text-xs bg-slate-100 border border-slate-200 rounded text-slate-500 font-mono cursor-not-allowed"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors shadow-sm"
              >
                <Save className="w-3.5 h-3.5" /> Save Admin Details
              </button>
            </div>
          </form>

          {/* Section 2: Admin Change Password via Mobile/Email OTP */}
          <form onSubmit={handleVerifyOTP} className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-slate-700" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Change Password via Mobile / Email OTP
                </h3>
              </div>

              {passwordSuccess && (
                <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Password Updated!
                </span>
              )}
            </div>

            {errorMsg && (
              <div className="p-2.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-xs font-medium">
                {errorMsg}
              </div>
            )}

            {!otpSent ? (
              <div className="p-3 rounded bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-900">Request Verification Code</div>
                  <div className="text-[11px] text-slate-500">
                    Send a 6-digit OTP code to <span className="font-bold">{email || mobile || 'Registered Email/Mobile'}</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleSendOTP}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-slate-900 bg-white border border-slate-300 rounded hover:bg-slate-50"
                >
                  <Send className="w-3.5 h-3.5" /> Send OTP
                </button>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div className="p-2.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px]">
                  ✓ OTP verification code sent! (Use demo OTP code: <code className="font-bold">123456</code>)
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Enter 6-Digit OTP Code
                    </label>
                    <input
                      type="text"
                      maxLength="6"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                      placeholder="123456"
                      className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono tracking-widest text-center"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      New Admin Password
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors shadow-sm"
                  >
                    <Key className="w-3.5 h-3.5" /> Verify OTP & Update Password
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      ) : (
        /* Employee Read-Only Profile View */
        <div className="p-6 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4 text-xs">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
            <img
              src={currentUser?.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser?.name || 'Employee')}&background=0f172a&color=fff`}
              alt={currentUser?.name}
              className="w-12 h-12 rounded-full border border-slate-200 object-cover"
            />
            <div>
              <h3 className="text-sm font-bold text-slate-900">{currentUser?.name}</h3>
              <p className="text-[11px] text-slate-500">{currentUser?.role || 'Employee'}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] text-slate-400">Username</div>
              <div className="font-mono font-bold text-slate-900">@{currentUser?.username}</div>
            </div>

            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] text-slate-400">Email Address</div>
              <div className="font-semibold text-slate-900">{currentUser?.email}</div>
            </div>

            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] text-slate-400">Mobile Number</div>
              <div className="font-mono font-semibold text-slate-900">{currentUser?.mobile || 'Not set'}</div>
            </div>

            <div className="p-3 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] text-slate-400">Account Status</div>
              <div className="font-bold text-emerald-600">Active Employee</div>
            </div>
          </div>

          <div className="p-3.5 rounded bg-slate-50 border border-slate-200 text-slate-600 flex items-start gap-2 text-[11px] mt-4">
            <Lock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Employee Read-Only Profile: </span>
              Your account details and login credentials are managed exclusively by the System Administrator. Contact your Admin to update your email, mobile number, or password.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
