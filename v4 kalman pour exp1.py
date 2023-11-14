import numpy as np
import matplotlib.pyplot as plt
import csv
import pandas as pd

class Kalman:
    def __init__(self,X0,P0,precision_baro_m=1, precision_gps_vz_ms=0.2,
                 bruit_modele_z_m=2, bruit_modele_vz_ms=4):
        """X:matrice d'estimation(position,vitesse);
        P:matrice de covariance ;
        F:matrice d'état;
        a:accélération(facteur extérieur);
        Q:facteur de covariance;
        R:estimation capteur;
        Z:covariance capteur;"""
        self.P0 = P0
        self.X0 = X0

        # R = [sigma_z² 0        ]
        #     [0        sigma_vz²]

        self.R = np.diag([precision_baro_m**2, precision_gps_vz_ms**2])
        self.Q = np.diag([bruit_modele_z_m**2, bruit_modele_vz_ms**2])
        self.innov = None
        self.innov_alt = 0
        self.innov_vz = 0
        H = np.eye(2)  # Identité d'ordre 2
        # La mesure est identique (en unité, en rapport) à l'état, donc X = Z = HZ >> H = I2
        # en effet, ce qu'on mesure est directement l'état (coup de chance).
        self.init_filter()

        self.record = {"t": [],
                       "alt_est": [],
                       "vz_est": [],
                       "sigma_alt_m": [],
                       "sigma_vz_ms": [],
                       "innov_alt_m": [],
                       "innov_vz_ms": []}

    def init_filter(self):
        self.P = self.P0.copy()
        self.X = self.X0.copy()

    def predict(self, dt):
        # B = facteur extérieur : B=np.array([[(dt**2)/2],[dt]])  à ajouter à X. Inutile ici.

        # definition
        F=np.array([[1,-dt],[0,1]])
        Ft=np.transpose(F)

        # système
        self.X=np.dot(F,self.X)                               # X= F*X+B"
        self.P=np.dot(np.dot(F,self.P),Ft) + self.Q*dt**2     # P = F*P*Ft+Q"
        self.record_filter(t)

    def update_2D(self, Alt_mes, Vz_mes): # Pour fusionner simultanément altitude et vitesse GPS
        '''
        H =  Identité d'ordre 2
        Z = la mesure (à mettre en entrée de la fonction)
        innovation = mesure expérimentale - mesure attendue '''

        # definition
        Z = np.array([[Alt_mes],[Vz_mes]])
        H = np.eye(2)
        Ht = np.transpose(H)

        self.innov = Z - np.dot(H, self.X)  # H.X =  Z prédit !
        cov_innov = np.dot(np.dot(H,self.P),Ht)+self.R

        # système

        K = self.P @ Ht @ np.linalg.inv(cov_innov)    # K final = Ft*P*inv(F*P*Ht+R)"
        self.X = self.X + K @ self.innov              # X final = x+Kf*(Z-H*X) = x + K * innov
        self.P = self.P - K @ H @ self.P              # P final = P -(Kfinale*F*P)"

    def update_alt(self, alt_mes, t):
        '''
        H =  [1, 0] : sélectionne l'état d'altitude
        Z = la mesure (à mettre en entrée de la fonction)
        innovation = mesure expérimentale - mesure attendue '''

        # definition
        Z = alt_mes
        H = np.array([[1, 0]])
        Ht = np.transpose(H)

        self.innov_alt = Z - np.dot(H, self.X)  # H.X =  Z prédit = Alt !
        cov_innov = np.dot(np.dot(H,self.P),Ht) + self.R[0][0]

        # système
        K = self.P @ Ht @ np.linalg.inv(cov_innov)    # Kfinale = Ft*P*inv(F*P*Ht+R)"
        K0 = np.squeeze(K) # dimensions 1D
        self.X = self.X + K0 * self.innov_alt              # Xfinale = x+Kf*(Z-H*X) = x + K * innov
        self.P = self.P - K @ H @ self.P              # Pfinale = P -(Kfinale*F*P)"

        self.record_filter(t, inn_alt=self.innov_alt)


    def update_vz(self, vz_mes, t):
        '''
        H =  [0, 1] : sélectionne l'état de vz
        Z = la mesure (à mettre en entrée de la fonction)
        innovation = mesure expérimentale - mesure attendue '''

        # definition
        Z = vz_mes
        H = np.array([[0, 1]])
        Ht = np.transpose(H)

        self.innov_vz = Z - np.dot(H, self.X)  # H.X =  Z prédit = VZ !
        cov_innov = np.dot(np.dot(H,self.P),Ht) + self.R[1][1]

        # système
        K = self.P @ Ht @ np.linalg.inv(cov_innov)    # Kfinale = Ft*P*inv(F*P*Ht+R)"
        K0 = np.squeeze(K) # dimensions 1D
        self.X = self.X + K0 * self.innov_vz              # Xfinale = x+Kf*(Z-H*X) = x + K * innov
        self.P = self.P - K @ H @ self.P              # Pfinale = P -(Kfinale*F*P)"
        self.record_filter(t, inn_vz=self.innov_vz)

    def record_filter(self, t, inn_alt=np.nan, inn_vz=np.nan):
        self.record["t"].append(t)
        self.record["alt_est"].append(self.X[0])
        self.record["vz_est"].append(self.X[1])
        self.record["sigma_alt_m"].append(np.sqrt(self.P[0][0]))
        self.record["sigma_vz_ms"].append(np.sqrt(self.P[1][1]))
        self.record["innov_alt_m"].append(np.squeeze(inn_alt))
        self.record["innov_vz_ms"].append(np.squeeze(inn_vz))

    def get_record_df(self):
        return pd.DataFrame(self.record)


if __name__ == "__main__":
    GPS_path = 'DJIFlightRecord_2021-11-06 alpha.csv'
    gps = pd.read_csv(GPS_path)

    Baro_path = 'DJIFlightRecord_2021-11-06 alpha.csv'
    baro = pd.read_csv(Baro_path)

    X0 = np.array([0, 0])
    P0 = np.diag([0.01,0.01])  #P0 ini : précision alt : 0.1m et 0.1m/s(0.01 = 0.1m*0.1m)

    t_gps = gps.timestamp
    alt_gps = gps.Alt_VPS
    vz_gps = gps.VZ

    t_baro = baro.timestamp
    alt_baro = baro.Alt_Baro

    kalman = Kalman(X0, P0, precision_baro_m=0.5, precision_gps_vz_ms=0.2,
                    bruit_modele_z_m=0.0, bruit_modele_vz_ms=2) # il faut remplir ici toutes les valeurs d'init de la classe

    loop = {"n_baro": 0,
            "n_gps": 0}

    t_final = max([t_baro.max(), t_gps.max()])
    t_ini = min([t_baro.min(), t_gps.min()])
    current_time = t_ini

    while current_time < t_final:
        t_baro_next = t_baro.iloc[loop["n_baro"]]
        t_gps_next = t_gps.iloc[loop["n_gps"]]
        if t_baro_next < t_gps_next:
            t = t_baro_next
            if t > current_time:
                dt = t - current_time
                kalman.predict(dt)
                current_time = t
            # a baro meas. arrived ! update altitude !
            kalman.update_alt(baro.Alt_Baro.iloc[loop["n_baro"]], t)
            loop['n_baro'] += 1
            # print(f"baro {loop['n_baro']}")
        else:
            t = t_gps_next
            if t > current_time:
                dt = t - current_time
                kalman.predict(dt)
                current_time = t
            # a gps meas. arrived ! update VZ !
            kalman.update_vz(gps.VZ.iloc[loop["n_gps"]], t)
            loop['n_gps'] += 1
            # print(f"gps {loop['n_gps']}")

        if loop['n_baro'] >= len(t_baro):
            break

        if loop['n_gps'] >= len(t_gps):
            break

    record = kalman.get_record_df()

    df = pd.DataFrame(record)
    df.to_csv('csvkalm')
    
    t_est = record["t"]
    alt_est_up = record["alt_est"] + 3 * record["sigma_alt_m"]
    alt_est_down = record["alt_est"] - 3 * record["sigma_alt_m"]
    vz_est_up = record["vz_est"] + 3 * record["sigma_vz_ms"]
    vz_est_down = record["vz_est"] - 3 * record["sigma_vz_ms"]


    f, (a, b) = plt.subplots(2, 1, sharex=True)
    f.set_size_inches(10, 12)
    
    f.subplots_adjust(left = 0.1, bottom = 0.2, right = 1.0,
                      top = 0.9, wspace = 0, hspace = 0.5)
    
    a.plot(t_est, record["alt_est"],'-',label='alt estimée')
    a.plot(t_est, alt_est_up,'r--', lw=0.5, label='3 sigmas')
    a.plot(t_est, alt_est_down,'r--', lw=0.5)

    a.plot(t_baro, alt_baro,'.', ms=1, label='alt baro')
    a.plot(t_gps, alt_gps - alt_gps.iloc[0] + alt_baro.iloc[0],'.', ms=1, label='alt gps')

    a.grid(True)
    a.set_xlabel("Temps (en s)")
    a.set_ylabel("Altitude (en m)")
    a.legend(loc='best')
    
    b.plot(t_est, record["vz_est"],'',label='vitesse estimée')
    b.plot(t_est, vz_est_up,'r--', lw=0.5, label='3 sigmas')
    b.plot(t_est, vz_est_down,'r--', lw=0.5)

    b.plot(t_gps, vz_gps,'-',label='vitesse gps')
    b.grid(True)
    b.set_xlabel("Temps (en s)")
    b.set_ylabel("Vitesse (en m/s)")
    b.legend(loc='best')

    plt.show()
    

