import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserCheck, 
  UserX, 
  Trash2, 
  Lock, 
  Search,
  UserPlus,
  Shield
} from 'lucide-react';
import { fetchUsersList, updateUserStatus, removeUserAccount } from '../services/api';
import { AddEmployeeModal } from '../components/modals/AddEmployeeModal';

export function UserManagementView({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const isAdmin = currentUser?.role === 'ADMIN';

  const loadUsers = async () => {
    setLoading(true);
    const res = await fetchUsersList();
    if (res.success) {
      setUsers(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleToggleStatus = async (user) => {
    const newStatus = user.status === 'ACTIVE' ? 'BLOCKED' : 'ACTIVE';
    const res = await updateUserStatus(user.id, newStatus);
    if (res.success) {
      setUsers(users.map(u => u.id === user.id ? { ...u, status: newStatus } : u));
    }
  };

  const handleRemoveUser = async (userId) => {
    if (window.confirm('Are you sure you want to remove this employee account?')) {
      const res = await removeUserAccount(userId);
      if (res.success) {
        setUsers(users.filter(u => u.id !== userId));
      }
    }
  };

  const handleEmployeeCreated = (newEmployee) => {
    setUsers([...users, newEmployee]);
  };

  const filteredUsers = users.filter(u => 
    u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isAdmin) {
    return (
      <div className="p-12 text-center bg-white rounded-lg border border-slate-200 shadow-sm space-y-3">
        <Lock className="w-10 h-10 mx-auto text-rose-500" />
        <h2 className="text-base font-bold text-slate-900">Access Restricted</h2>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          The Employee Management panel is restricted exclusively to System Administrators. Regular employees cannot view or modify company user accounts.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              Employee Account Management
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-white">
              ADMIN PANEL
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Create employee accounts, assign login credentials, block/unblock users, and manage staff access.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search employees..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-md text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
            />
          </div>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors shadow-sm cursor-pointer shrink-0"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Create Employee Account</span>
          </button>
        </div>
      </div>

      {/* Users Table */}
      <div className="rounded-lg bg-white border border-slate-200 shadow-sm overflow-hidden">
        {filteredUsers.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Users className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium">No employee accounts found.</p>
            <p className="text-xs text-slate-400 mt-1">Click "Create Employee Account" above to add new staff members.</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Employee</th>
                <th className="py-3 px-4">Email</th>
                <th className="py-3 px-4 text-center">Role</th>
                <th className="py-3 px-4 text-center">Account Status</th>
                <th className="py-3 px-4 text-right">Admin Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-3">
                      <img
                        src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=0f172a&color=fff`}
                        alt={user.name}
                        className="w-8 h-8 rounded-full border border-slate-200 object-cover"
                      />
                      <div>
                        <div className="font-bold text-slate-900 text-xs">{user.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">@{user.username}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono">
                    {user.email}
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      user.role === 'ADMIN'
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-700 border border-slate-200'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      user.status === 'ACTIVE'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    {user.role !== 'ADMIN' ? (
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleToggleStatus(user)}
                          className={`inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${
                            user.status === 'ACTIVE'
                              ? 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100'
                              : 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
                          }`}
                        >
                          {user.status === 'ACTIVE' ? (
                            <><UserX className="w-3 h-3 text-amber-600" /> Block Account</>
                          ) : (
                            <><UserCheck className="w-3 h-3 text-emerald-600" /> Unblock</>
                          )}
                        </button>
                        <button
                          onClick={() => handleRemoveUser(user.id)}
                          className="p-1.5 rounded text-rose-600 hover:bg-rose-50 border border-rose-200 transition-colors"
                          title="Remove Employee Account"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <span className="text-[10px] text-slate-400 italic">Primary Admin</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Employee Modal */}
      <AddEmployeeModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onEmployeeCreated={handleEmployeeCreated}
      />
    </div>
  );
}
