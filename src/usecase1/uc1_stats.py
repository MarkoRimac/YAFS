from yafs.stats import Stats
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import linregress
import os
import shutil

class Uc1_stats(Stats):

    def __init__(self, config_version, app_version, runtime_time, **kwargs):
        super(Uc1_stats, self).__init__(**kwargs)
        self.config_version = config_version
        self.app_version = app_version
        self.runtime_time = runtime_time

    def uc1_do_stats(self):
        self.__uc1_service_utilizations()
        self.__uc1_end_to_end_time()
        self.__uc1_copy_config_file()

    def uc1_stats_save_gexf(self, topology, name):
        if not os.path.exists("output/" + "config" + self.config_version + "_" + self.app_version):
            os.makedirs("output/" + "config" + self.config_version + "_" + self.app_version)
        nx.write_gexf(topology.G, "output/" + "config" + self.config_version + "_" + self.app_version + '/' + name + '.gexf')

    def __uc1_service_utilizations(self):

        values = self.__get_df_service_utilization_with_des_id("GW", 5000)
        self.__uc1_plot_utilization(values, "GW")
        values = self.__get_df_service_utilization_with_des_id("NR_FILT", 5000)
        self.__uc1_plot_utilization(values, "NR_FILT")
        values = self.__get_df_service_utilization_with_des_id("NR_DECOMP", 5000)
        self.__uc1_plot_utilization(values, "NR_DECOMP")
        values = self.__get_df_service_utilization_with_des_id("DC_PROC", 5000)
        self.__uc1_plot_utilization(values, "DC_PROC")
        values = self.__get_df_service_utilization_with_des_id("DC_STORAGE", 5000)
        self.__uc1_plot_utilization(values, "DC_STORAGE")


    def __uc1_end_to_end_time(self):

        x = self.df[self.df['message'].isin(['MM_GW_m', 'DC_PROC_DC_STORAGE_m'])]
        x = x.drop_duplicates(['id', 'message'])    #  Dropaj one poruke koje su se slale na vise GW-a, ostavi samo jednu
        x = x.loc[:, ['id', 'message', 'time_emit']]

        id_x_list = list()
        time_y_list = list()
        id_x_no_list = list() #  id poruka koje nisu uspjele doci do kraja.
        time_y_no_list = list()
        for id in x['id']:

            time_in = x[x['id'] == id]['time_emit'].values[0]
            try:
                result_time = x[x['id'] == id]['time_emit'].values[1] - time_in
                id_x_list.append(time_in)
                time_y_list.append(result_time)
            except IndexError:
                id_x_no_list.append(time_in)
                result_time = 'NaN'
                time_y_no_list.append(-1)

        stats = linregress(id_x_list, time_y_list)

        m = stats.slope
        b = stats.intercept

        plt.clf()
        plt.scatter(id_x_list, time_y_list)
        plt.plot(id_x_list, m * np.array(id_x_list, dtype=float) + b, color="red")
        plt.scatter(id_x_no_list, len(id_x_no_list)*[0], color="red", marker="x")
        plt.xlabel("Time in")
        plt.ylabel("Time spent in system")
        if not os.path.exists("output/" + "config" + self.config_version + "_" + self.app_version):
            os.makedirs("output/" + "config" + self.config_version + "_" + self.app_version)
        plt.savefig("output/" + "config" + self.config_version + "_" + self.app_version + "/end_to_end.png", dpi=300)

        plt.clf()

        plt.ylabel('broj poruka')
        plt.xlabel('vrijeme od izvora do ponora')
        plt.locator_params(axis='y', integer=True)
        num_bins = 11
        plt.xticks(np.arange(-500, self.runtime_time + 1, (self.runtime_time+500)/num_bins))
        n, bins, patches = plt.hist(time_y_list + time_y_no_list,  num_bins, facecolor='blue', range=[-500,self.runtime_time], alpha=1)
        patches[0].set_facecolor('r')

        if not os.path.exists("output/" + "config" + self.config_version + "_" + self.app_version):
            os.makedirs("output/" + "config" + self.config_version + "_" + self.app_version)
        plt.savefig("output/" + "config" + self.config_version + "_" + self.app_version + "/end_to_end_utilization_histo.png", dpi=300)

        plt.clf()


    def __get_df_service_utilization_with_des_id(self,service,time):
        """
        Returns the utilization(%) of a specific module
        """
        g = self.df.groupby(["module", "DES.dst"]).agg({"service": ['mean', 'sum', 'count']})
        g.reset_index(inplace=True)
        h = pd.DataFrame()
        h["module"] = g[g.module == service].module
        h["utilization"] = g[g.module == service]["service"]["sum"]*100 / time
        h["DES_id"] = g[g.module == service]["DES.dst"]
        return h

    def __uc1_plot_utilization(self, values, node_type):

        plt.clf()

        bar_x = values["DES_id"].to_numpy().tolist()
        bar_y = values["utilization"].to_numpy().tolist()
        bar_label = [str(i) for i in values["DES_id"].to_numpy().tolist()]
        plt.ylim([0, 100])
        plt.bar(bar_x, bar_y, tick_label=bar_label)
        plt.xlabel(node_type + " DES ids")
        plt.ylabel("Utilization (%)")

        if not os.path.exists("output/" + "config" + self.config_version+ "_" + self.app_version):
            os.makedirs("output/" + "config" + self.config_version + "_" + self.app_version)
        plt.savefig("output/" + "config" + self.config_version + "_" + self.app_version + "/" + node_type + "_utilization.png", dpi=300)

        plt.clf()

        plt.ylabel('number of modules')
        plt.xlabel('utilization in %')
        plt.locator_params(axis='y', integer=True)
        num_bins = 20
        plt.xticks(np.arange(0, 100 + 1, 5))
        n, bins, patches = plt.hist(values["utilization"].to_numpy().tolist(),  num_bins, range=[0, 100], facecolor='blue', alpha=1)
        if not os.path.exists("output/" + "config" + self.config_version + "_" + self.app_version):
            os.makedirs("output/" + "config" + self.config_version + "_" + self.app_version)
        plt.savefig("output/" + "config" + self.config_version + "_" + self.app_version + "/" + node_type + "_utilization_histo.png", dpi=300)

        plt.clf()

    def __uc1_copy_config_file(self):
        if not os.path.exists("output/" + "config" + self.config_version + "_" + self.app_version):
            os.makedirs("output/" + "config" + self.config_version + "_" + self.app_version)
        shutil.copy('config.json', "output/" + "config" + self.config_version + "_" + self.app_version)