import React, { useState } from 'react';
import {
  Building2,
  Plus,
  Search,
  Edit2,
  Trash2,
  Eye,
  CheckCircle2,
  AlertCircle,
  X,
  FileText,
  Truck,
  Repeat,
  Loader2,
  ShieldCheck,
  Phone,
  Mail,
  MapPin
} from 'lucide-react';
import {
  useCustomersQuery,
  useCustomerTiersQuery,
  useCreateCustomerMutation,
  useUpdateCustomerMutation,
  useDeleteCustomerMutation,
  useCustomerQuotationsQuery,
  useCustomerOrdersQuery,
  useCustomerSubscriptionsQuery
} from '../../hooks/useBackendData';
import { CustomerResponse, CustomerCreateRequest, CustomerUpdateRequest } from '../../types';
import { useApp } from '../../context/AppContext';

export const CustomerManagementPanel: React.FC = () => {
  const { showNotification, refreshBackendCustomers } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTierFilter, setSelectedTierFilter] = useState('');

  // Queries
  const {
    data: customers = [],
    isLoading: isCustomersLoading,
    error: customersError,
    refetch: refetchCustomers
  } = useCustomersQuery({
    search: searchQuery.trim() || undefined,
    customer_tier_id: selectedTierFilter || undefined,
  });

  const { data: customerTiers = [] } = useCustomerTiersQuery({ is_active: true });

  // Mutations
  const createCustomerMutation = useCreateCustomerMutation();
  const updateCustomerMutation = useUpdateCustomerMutation();
  const deleteCustomerMutation = useDeleteCustomerMutation();

  // Modal States
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [customerToEdit, setCustomerToEdit] = useState<CustomerResponse | null>(null);
  const [selectedCustomerForHistory, setSelectedCustomerForHistory] = useState<CustomerResponse | null>(null);

  // Form States for Create
  const [newName, setNewName] = useState('');
  const [newTierId, setNewTierId] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newBillingAddress, setNewBillingAddress] = useState('');
  const [newShippingAddress, setNewShippingAddress] = useState('');
  const [newIsActive, setNewIsActive] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  // Form States for Edit
  const [editName, setEditName] = useState('');
  const [editTierId, setEditTierId] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editPhone, setEditPhone] = useState('');
  const [editBillingAddress, setEditBillingAddress] = useState('');
  const [editShippingAddress, setEditShippingAddress] = useState('');
  const [editIsActive, setEditIsActive] = useState(true);
  const [editFormError, setEditFormError] = useState<string | null>(null);

  // History Drawer Tab
  const [historyTab, setHistoryTab] = useState<'QUOTES' | 'ORDERS' | 'SUBS'>('QUOTES');

  // Customer History Queries
  const {
    data: customerQuotes = [],
    isLoading: isQuotesLoading
  } = useCustomerQuotationsQuery(selectedCustomerForHistory?.id || '');

  const {
    data: customerOrders = [],
    isLoading: isOrdersLoading
  } = useCustomerOrdersQuery(selectedCustomerForHistory?.id || '');

  const {
    data: customerSubs = [],
    isLoading: isSubsLoading
  } = useCustomerSubscriptionsQuery(selectedCustomerForHistory?.id || '');

  // Tier lookup map
  const tierMap = new Map(customerTiers.map(t => [t.id, t.name]));

  const handleOpenAdd = () => {
    setNewName('');
    setNewTierId(customerTiers[0]?.id || '');
    setNewEmail('');
    setNewPhone('');
    setNewBillingAddress('');
    setNewShippingAddress('');
    setNewIsActive(true);
    setFormError(null);
    setIsAddOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) {
      setFormError('Customer name is required.');
      return;
    }
    if (!newTierId) {
      setFormError('Please select a customer tier.');
      return;
    }

    const payload: CustomerCreateRequest = {
      name: newName.trim(),
      customer_tier_id: newTierId,
      email: newEmail.trim() || undefined,
      phone: newPhone.trim() || undefined,
      billing_address: newBillingAddress.trim() || undefined,
      shipping_address: newShippingAddress.trim() || undefined,
      is_active: newIsActive,
    };

    try {
      await createCustomerMutation.mutateAsync(payload);
      showNotification(`Customer "${payload.name}" created successfully.`, 'success');
      setIsAddOpen(false);
      refreshBackendCustomers();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create customer record.');
    }
  };

  const handleOpenEdit = (c: CustomerResponse) => {
    setCustomerToEdit(c);
    setEditName(c.name);
    setEditTierId(c.customer_tier_id);
    setEditEmail(c.email || '');
    setEditPhone(c.phone || '');
    setEditBillingAddress(c.billing_address || '');
    setEditShippingAddress(c.shipping_address || '');
    setEditIsActive(c.is_active);
    setEditFormError(null);
    setIsEditOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerToEdit) return;
    if (!editName.trim()) {
      setEditFormError('Customer name is required.');
      return;
    }

    const payload: CustomerUpdateRequest = {
      name: editName.trim(),
      customer_tier_id: editTierId || undefined,
      email: editEmail.trim() || null,
      phone: editPhone.trim() || null,
      billing_address: editBillingAddress.trim() || null,
      shipping_address: editShippingAddress.trim() || null,
      is_active: editIsActive,
    };

    try {
      await updateCustomerMutation.mutateAsync({ id: customerToEdit.id, payload });
      showNotification(`Customer "${editName}" updated successfully.`, 'success');
      setIsEditOpen(false);
      refreshBackendCustomers();
    } catch (err: any) {
      setEditFormError(err?.message || 'Failed to update customer.');
    }
  };

  const handleDelete = async (c: CustomerResponse) => {
    if (window.confirm(`Are you sure you want to deactivate customer "${c.name}"?`)) {
      try {
        await deleteCustomerMutation.mutateAsync(c.id);
        showNotification(`Customer "${c.name}" deactivated.`, 'info');
        refreshBackendCustomers();
      } catch (err: any) {
        showNotification(err?.message || 'Failed to deactivate customer.', 'error');
      }
    }
  };

  return (
    <div className="space-y-5">
      {/* Top Filter & Actions Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex flex-1 items-center gap-3 w-full md:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search customers by name or contact..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Tier Filter */}
          <select
            value={selectedTierFilter}
            onChange={(e) => setSelectedTierFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg bg-slate-50 px-3 py-1.5 focus:bg-white focus:outline-hidden"
          >
            <option value="">All Customer Tiers</option>
            {customerTiers.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleOpenAdd}
          className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition cursor-pointer shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Add B2B Customer</span>
        </button>
      </div>

      {/* Customer Master Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">B2B Customer Accounts</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {customers.length} Accounts Registered
          </span>
        </div>

        {isCustomersLoading ? (
          <div className="p-12 text-center text-slate-500 text-xs flex flex-col items-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <span>Loading customers from PostgreSQL...</span>
          </div>
        ) : customersError ? (
          <div className="p-8 text-center text-red-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <p>Failed to load customers from backend API: {(customersError as any)?.message}</p>
            <button
              onClick={() => refetchCustomers()}
              className="mt-3 px-3 py-1 bg-red-50 border border-red-200 rounded text-red-700 hover:bg-red-100 font-semibold"
            >
              Retry
            </button>
          </div>
        ) : customers.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <Building2 className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p>No customers found matching the search filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                  <th className="py-3 px-4">Customer / Organization</th>
                  <th className="py-3 px-3">Tier Assignment</th>
                  <th className="py-3 px-3">Contact</th>
                  <th className="py-3 px-3">Address</th>
                  <th className="py-3 px-3 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {customers.map((c) => {
                  const tierName = tierMap.get(c.customer_tier_id) || 'STANDARD';
                  return (
                    <tr key={c.id} className="hover:bg-slate-50/60 transition">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{c.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">ID: {c.id.slice(0, 8)}...</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border bg-blue-50 text-blue-700 border-blue-200 font-mono">
                          <ShieldCheck className="w-3 h-3 text-blue-600" />
                          {tierName}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-600 space-y-0.5">
                        {c.email && (
                          <div className="flex items-center gap-1 text-[11px]">
                            <Mail className="w-3 h-3 text-slate-400" />
                            <span>{c.email}</span>
                          </div>
                        )}
                        {c.phone && (
                          <div className="flex items-center gap-1 text-[11px]">
                            <Phone className="w-3 h-3 text-slate-400" />
                            <span>{c.phone}</span>
                          </div>
                        )}
                        {!c.email && !c.phone && <span className="text-slate-400 italic">No contact</span>}
                      </td>
                      <td className="py-3 px-3 text-slate-500 text-[11px] max-w-xs truncate">
                        {c.billing_address || c.shipping_address ? (
                          <div className="flex items-center gap-1 truncate" title={c.billing_address || c.shipping_address || ''}>
                            <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                            <span className="truncate">{c.billing_address || c.shipping_address}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">None</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          c.is_active
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                        }`}>
                          {c.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1">
                        <button
                          onClick={() => setSelectedCustomerForHistory(c)}
                          title="Inspect Quotations, Orders, Subscriptions"
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleOpenEdit(c)}
                          title="Edit Customer"
                          className="p-1.5 text-slate-600 hover:bg-slate-100 rounded-md transition cursor-pointer"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(c)}
                          title="Deactivate Customer"
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Customer Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Add New B2B Customer Account</h3>
              </div>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
              {formError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Company / Account Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporation"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Customer Tier Ceiling *</label>
                <select
                  required
                  value={newTierId}
                  onChange={(e) => setNewTierId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500 bg-white"
                >
                  {customerTiers.map(t => (
                    <option key={t.id} value={t.id}>{t.name} (Max {t.default_discount_limit}% discount ceiling)</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Primary Email</label>
                  <input
                    type="email"
                    placeholder="contact@company.com"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Contact Phone</label>
                  <input
                    type="text"
                    placeholder="+1 (555) 000-0000"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Billing Address</label>
                <input
                  type="text"
                  placeholder="100 Enterprise Way, Suite 400, Austin TX"
                  value={newBillingAddress}
                  onChange={(e) => setNewBillingAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Shipping Address</label>
                <input
                  type="text"
                  placeholder="Distribution Center Dock 3, Chicago IL"
                  value={newShippingAddress}
                  onChange={(e) => setNewShippingAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="create-is-active"
                  checked={newIsActive}
                  onChange={(e) => setNewIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="create-is-active" className="text-slate-700 font-medium">
                  Active account eligible for quotations
                </label>
              </div>

              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-white font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createCustomerMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-xs flex items-center gap-1.5"
                >
                  {createCustomerMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Customer</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Customer Modal */}
      {isEditOpen && customerToEdit && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Edit Customer: {customerToEdit.name}</h3>
              </div>
              <button onClick={() => setIsEditOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-6 space-y-4 text-xs">
              {editFormError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{editFormError}</span>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Company / Account Name *</label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Customer Tier</label>
                <select
                  value={editTierId}
                  onChange={(e) => setEditTierId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500 bg-white"
                >
                  {customerTiers.map(t => (
                    <option key={t.id} value={t.id}>{t.name} (Max {t.default_discount_limit}% discount ceiling)</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={editEmail}
                    onChange={(e) => setEditEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={editPhone}
                    onChange={(e) => setEditPhone(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Billing Address</label>
                <input
                  type="text"
                  value={editBillingAddress}
                  onChange={(e) => setEditBillingAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Shipping Address</label>
                <input
                  type="text"
                  value={editShippingAddress}
                  onChange={(e) => setEditShippingAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="edit-is-active"
                  checked={editIsActive}
                  onChange={(e) => setEditIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="edit-is-active" className="text-slate-700 font-medium">
                  Active Status
                </label>
              </div>

              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-white font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateCustomerMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-xs flex items-center gap-1.5"
                >
                  {updateCustomerMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Customer Commercial History Drawer / Modal */}
      {selectedCustomerForHistory && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-3xl w-full overflow-hidden flex flex-col max-h-[85vh]">
            {/* Header */}
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-blue-600" />
                  <h3 className="text-base font-bold text-slate-900">{selectedCustomerForHistory.name}</h3>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-mono font-bold border border-blue-200">
                    {tierMap.get(selectedCustomerForHistory.customer_tier_id) || 'TIER'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Customer UUID: <span className="font-mono text-slate-700">{selectedCustomerForHistory.id}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedCustomerForHistory(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-Navigation Tabs */}
            <div className="flex border-b border-slate-200 px-6 bg-slate-50/50 text-xs font-semibold gap-4">
              <button
                onClick={() => setHistoryTab('QUOTES')}
                className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
                  historyTab === 'QUOTES' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Quotations ({customerQuotes.length})</span>
              </button>

              <button
                onClick={() => setHistoryTab('ORDERS')}
                className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
                  historyTab === 'ORDERS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Truck className="w-3.5 h-3.5" />
                <span>Orders ({customerOrders.length})</span>
              </button>

              <button
                onClick={() => setHistoryTab('SUBS')}
                className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
                  historyTab === 'SUBS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Repeat className="w-3.5 h-3.5" />
                <span>Subscriptions ({customerSubs.length})</span>
              </button>
            </div>

            {/* Tab Body */}
            <div className="p-6 overflow-y-auto flex-1 text-xs">
              {historyTab === 'QUOTES' && (
                <div>
                  {isQuotesLoading ? (
                    <div className="py-8 text-center text-slate-500 flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                      <span>Fetching customer quotation records...</span>
                    </div>
                  ) : customerQuotes.length === 0 ? (
                    <p className="text-center text-slate-400 py-8 italic">No quotations found for this account.</p>
                  ) : (
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 text-[10px] uppercase">
                          <th className="py-2">Quote #</th>
                          <th className="py-2">Status</th>
                          <th className="py-2 text-right">Total</th>
                          <th className="py-2 text-right">Margin %</th>
                          <th className="py-2 text-right">Risk</th>
                          <th className="py-2 text-right">Created</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono">
                        {customerQuotes.map(q => (
                          <tr key={q.id} className="hover:bg-slate-50">
                            <td className="py-2.5 font-bold text-blue-700">{q.quotation_number}</td>
                            <td className="py-2.5"><span className="text-[10px] px-2 py-0.5 rounded bg-slate-100">{q.status}</span></td>
                            <td className="py-2.5 text-right font-bold text-slate-900">${Number(q.total_amount).toLocaleString()}</td>
                            <td className="py-2.5 text-right text-emerald-700">{Number(q.margin_percent)}%</td>
                            <td className="py-2.5 text-right">{q.risk_score}</td>
                            <td className="py-2.5 text-right text-slate-400 text-[11px] font-sans">
                              {new Date(q.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {historyTab === 'ORDERS' && (
                <div>
                  {isOrdersLoading ? (
                    <div className="py-8 text-center text-slate-500 flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                      <span>Fetching customer order records...</span>
                    </div>
                  ) : customerOrders.length === 0 ? (
                    <p className="text-center text-slate-400 py-8 italic">No fulfilled orders recorded for this account.</p>
                  ) : (
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 text-[10px] uppercase">
                          <th className="py-2">Order #</th>
                          <th className="py-2">Status</th>
                          <th className="py-2 text-right">Total Amount</th>
                          <th className="py-2 text-right">Created</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono">
                        {customerOrders.map(o => (
                          <tr key={o.id} className="hover:bg-slate-50">
                            <td className="py-2.5 font-bold text-purple-700">{o.order_number}</td>
                            <td className="py-2.5"><span className="text-[10px] px-2 py-0.5 rounded bg-purple-50 text-purple-700">{o.status}</span></td>
                            <td className="py-2.5 text-right font-bold text-slate-900">${Number(o.total_amount).toLocaleString()}</td>
                            <td className="py-2.5 text-right text-slate-400 text-[11px] font-sans">
                              {new Date(o.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {historyTab === 'SUBS' && (
                <div>
                  {isSubsLoading ? (
                    <div className="py-8 text-center text-slate-500 flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                      <span>Fetching customer recurring subscriptions...</span>
                    </div>
                  ) : customerSubs.length === 0 ? (
                    <p className="text-center text-slate-400 py-8 italic">No active recurring subscriptions found.</p>
                  ) : (
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 text-[10px] uppercase">
                          <th className="py-2">Plan ID</th>
                          <th className="py-2">Status</th>
                          <th className="py-2 text-center">Qty</th>
                          <th className="py-2 text-right">Rate</th>
                          <th className="py-2 text-right">Next Billing</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono">
                        {customerSubs.map(s => (
                          <tr key={s.id} className="hover:bg-slate-50">
                            <td className="py-2.5 text-slate-800">{s.plan_id.slice(0, 8)}...</td>
                            <td className="py-2.5"><span className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">{s.status}</span></td>
                            <td className="py-2.5 text-center">{s.quantity}</td>
                            <td className="py-2.5 text-right font-bold">${Number(s.unit_price).toLocaleString()}</td>
                            <td className="py-2.5 text-right text-slate-500">{s.next_billing_date}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
