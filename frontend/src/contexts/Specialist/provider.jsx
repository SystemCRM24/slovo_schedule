import React from "react";
import {SpecialistContext} from "./context.js";

export function SpecialistContextProvider({children, specialist}) {
    return <SpecialistContext.Provider value={specialist}>{children}</SpecialistContext.Provider>
}

export function useSpecialistContext() {
    const context = React.useContext(SpecialistContext);
    if (!context) throw new Error('Use context within provider!');
    return context;
}
