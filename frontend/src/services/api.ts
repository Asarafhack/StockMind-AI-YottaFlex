import axios from 'axios';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface KPIOverviewData {
  total_skus: number;
  total_locations: number;
  total_on_hand_inventory: number;
  available_to_promise_quantity: number;
  active_reservations: number;
  in_transit_inventory: number;
  open_orders: number;
  fulfillment_rate_pct: number;
  inventory_accuracy_pct: number;
  total_anomalies: number;
  critical_anomalies: number;
  open_anomalies: number;
  stockout_rate_pct: number;
  reservation_expiry_rate_pct: number;
}

export interface InventoryBalanceItem {
  balance_id: string;
  sku_id: string;
  location_id: string;
  on_hand_quantity: number;
  reserved_quantity: number;
  blocked_quantity: number;
  safety_stock_quantity: number;
  in_transit_quantity: number;
  available_quantity: number;
  last_movement_id: string | null;
  version: number;
  updated_at: string;
}

export interface ATPData {
  sku_id: string;
  location_id: string;
  on_hand_stock: number;
  reserved_stock: number;
  blocked_stock: number;
  safety_stock: number;
  eligible_inbound: number;
  final_atp: number;
  reservable_stock: number;
  calculation_timestamp: string;
  source_movement_references: string[];
  explanatory_decision_reason: string;
}

export interface AnomalyItem {
  anomaly_id: string;
  issue_type: string;
  entity_type: string;
  entity_id: string;
  affected_sku: string | null;
  affected_location: string | null;
  detection_timestamp: string;
  expected_value: string;
  observed_value: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  explanation: string;
  recommended_action: string;
  ground_truth_label: string | null;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  resolved_at: string | null;
  resolved_by: string | null;
}

export interface OrderItem {
  order_id: string;
  channel: string;
  customer_reference: string;
  order_status: string;
  order_date: string;
  requested_delivery_date: string | null;
  fulfillment_location_id: string | null;
  total_amount: number;
  currency: string;
  order_lines: Array<{
    order_line_id: string;
    sku_id: string;
    ordered_quantity: number;
    allocated_quantity: number;
    fulfilled_quantity: number;
    unit_price: number;
    line_status: string;
  }>;
}

export interface TransferItem {
  transfer_id: string;
  transfer_number: string;
  source_location_id: string;
  destination_location_id: string;
  status: string;
  requested_at: string;
  dispatched_at: string | null;
  received_at: string | null;
  carrier: string | null;
  tracking_reference: string | null;
  notes: string | null;
  transfer_lines: Array<{
    transfer_line_id: string;
    sku_id: string;
    requested_quantity: number;
    dispatched_quantity: number;
    received_quantity: number;
  }>;
}

// API functions
export const fetchOverviewKPIs = async (): Promise<KPIOverviewData> => {
  const { data } = await apiClient.get<KPIOverviewData>('/analytics/overview');
  return data;
};

export const fetchInventoryBalances = async (params?: {
  sku_id?: string;
  location_id?: string;
  status?: string;
  limit?: number;
}): Promise<InventoryBalanceItem[]> => {
  const { data } = await apiClient.get<InventoryBalanceItem[]>('/inventory', { params });
  return data;
};

export const fetchATPBreakdown = async (sku_id: string, location_id: string, protect_safety: boolean = false): Promise<ATPData> => {
  const { data } = await apiClient.get<ATPData>(`/inventory/${sku_id}/${location_id}/atp`, {
    params: { protect_safety_stock: protect_safety }
  });
  return data;
};

export const reconcileBalance = async (sku_id: string, location_id: string) => {
  const { data } = await apiClient.post(`/inventory/${sku_id}/${location_id}/reconcile`);
  return data;
};

export const applyCompensatingAdjustment = async (sku_id: string, location_id: string) => {
  const { data } = await apiClient.post(`/inventory/${sku_id}/${location_id}/compensate`);
  return data;
};

export const fetchAnomalies = async (params?: { status?: string; severity?: string; issue_type?: string }): Promise<AnomalyItem[]> => {
  const { data } = await apiClient.get<AnomalyItem[]>('/anomalies', { params });
  return data;
};

export const triggerAnomalyScan = async () => {
  const { data } = await apiClient.post('/anomalies/scan');
  return data;
};

export const acknowledgeAnomaly = async (anomaly_id: string) => {
  const { data } = await apiClient.post(`/anomalies/${anomaly_id}/acknowledge`);
  return data;
};

export const resolveAnomaly = async (anomaly_id: string, notes?: string) => {
  const { data } = await apiClient.post(`/anomalies/${anomaly_id}/resolve`, null, {
    params: { resolution_notes: notes || 'Resolved from dashboard' }
  });
  return data;
};

export const autoHealAnomaly = async (anomaly_id: string) => {
  const { data } = await apiClient.post(`/anomalies/${anomaly_id}/auto-heal`);
  return data;
};

export const fetchOrders = async (limit: number = 50): Promise<OrderItem[]> => {
  const { data } = await apiClient.get<OrderItem[]>('/orders', { params: { limit } });
  return data;
};

export const allocateOrder = async (order_id: string) => {
  const { data } = await apiClient.post(`/orders/${order_id}/allocate`);
  return data;
};

export const fulfillOrder = async (order_id: string) => {
  const { data } = await apiClient.post(`/orders/${order_id}/fulfill`);
  return data;
};

export const fetchTransfers = async (): Promise<TransferItem[]> => {
  const { data } = await apiClient.get<TransferItem[]>('/transfers');
  return data;
};

export const dispatchTransfer = async (transfer_id: string) => {
  const { data } = await apiClient.post(`/transfers/${transfer_id}/dispatch`);
  return data;
};

export const receiveTransfer = async (transfer_id: string) => {
  const { data } = await apiClient.post(`/transfers/${transfer_id}/receive`);
  return data;
};

export const fetchReplenishmentRecommendations = async () => {
  const { data } = await apiClient.get('/replenishment/recommendations');
  return data;
};

export const runWhatIfSimulation = async (demandSurgePct: number, delayDays: number) => {
  const { data } = await apiClient.get('/analytics/what-if/simulate', {
    params: { demand_surge_pct: demandSurgePct, lead_time_delay_days: delayDays }
  });
  return data;
};

export const triggerGeneratorJob = async (profile: 'starter' | 'full', seed: number = 20261022) => {
  const { data } = await apiClient.post('/generator/jobs', {
    profile,
    seed,
    batch_size: 1000,
    include_anomalies: true,
    output_formats: ['csv', 'json', 'parquet']
  });
  return data;
};

export const fetchGeneratorJobStatus = async (job_id: string) => {
  const { data } = await apiClient.get(`/generator/jobs/${job_id}`);
  return data;
};

export const fetchValidationReport = async () => {
  const { data } = await apiClient.get('/validation/reports');
  return data;
};

export const fetchLocationCharts = async () => {
  const { data } = await apiClient.get('/analytics/charts/location-distribution');
  return data;
};

export const fetchCategoryCharts = async () => {
  const { data } = await apiClient.get('/analytics/charts/category-distribution');
  return data;
};

export const fetchAuditLogs = async (limit: number = 50) => {
  const { data } = await apiClient.get('/audit/logs', { params: { limit } });
  return data;
};
