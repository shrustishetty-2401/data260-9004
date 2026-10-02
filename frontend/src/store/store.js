import { configureStore } from "@reduxjs/toolkit";
import reportsReducer from "./reportSlice";

const store = configureStore({
  reducer: {
    reports: reportsReducer,
  },
});

export default store;