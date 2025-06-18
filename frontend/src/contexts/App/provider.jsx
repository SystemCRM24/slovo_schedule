import React, { useState } from "react";
import { AppContext } from "./context.js";

export const AppContextProvider = ({ children }) => {
    const [dates, setDates] = useState({ fromDate: undefined, toDate: undefined });

    return (
        <AppContext.Provider value={{ dates, setDates }}>
            {children}
        </AppContext.Provider>
    );
};