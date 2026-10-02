import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import {
  createReport,
  deleteReport,
  getReports,
  updateReport,
} from "../api";

export const fetchReports = createAsyncThunk(
  "reports/fetchReports",
  async ({ skip = 0, limit = 10 } = {}) => {
    return await getReports(skip, limit);
  },
);

export const addReport = createAsyncThunk(
  "reports/addReport",
  async (payload) => {
    return await createReport(payload);
  },
);

export const editReport = createAsyncThunk(
  "reports/editReport",
  async ({ id, payload }) => {
    return await updateReport(id, payload);
  },
);

export const removeReport = createAsyncThunk(
  "reports/removeReport",
  async (id) => {
    await deleteReport(id);
    return id;
  },
);

const initialState = {
  items: [],
  status: "idle",
  error: null,
};

const reportSlice = createSlice({
  name: "reports",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchReports.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchReports.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchReports.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(addReport.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      })
      .addCase(editReport.fulfilled, (state, action) => {
        const index = state.items.findIndex(
          (item) => item.id === action.payload.id,
        );

        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(removeReport.fulfilled, (state, action) => {
        state.items = state.items.filter(
          (item) => item.id !== action.payload,
        );
      });
  },
});

export default reportSlice.reducer;