#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

''' Initialize with default environment variables '''
__name__ = "sparkCleanNRich"
__module__ = "etl"
__package__ = "transform"
__app__ = "utils"
__ini_fname__ = "app.ini"
__conf_fname__ = "app.cfg"

''' Load necessary and sufficient python librairies that are used throughout the class'''
try:
    import os
    import sys
    import configparser    
    import logging
    import traceback

    import findspark
    findspark.init()
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    from pyspark.ml.feature import Imputer
    from pyspark.sql import DataFrame

    print("All functional %s-libraries in %s-package of %s-module imported successfully!"
          % (__name__.upper(),__package__.upper(),__module__.upper()))

except Exception as e:
    print("Some packages in {0} module {1} package for {2} function didn't load\n{3}"\
          .format(__module__.upper(),__package__.upper(),__name__.upper(),e))

'''
    CLASS Enrich and Clean pyspark dataframes. Utility for data governance data standardization.

    Contributor(s):
        * nuwan.waidyanatha@rezgateway.com

    Resources: 
        Data Governance in Wiki: https://tinyurl.com/rezaware-datagovernance
'''
class Transformer():
    ''' Function
            name: __init__
            parameters:
                    @name (str)
                    @enrich (dict)
            procedure: 
            return None
            
            author: <nuwan.waidyanatha@rezgateway.com>

    '''
    def __init__(self, desc : str="spark workloads",   # identifier for the instances
                 **kwargs:dict,   # can contain hostIP and database connection settings
                ):

        self.__name__ = __name__
        self.__package__ = __package__
        self.__module__ = __module__
        self.__app__ = __app__
        self.__ini_fname__ = __ini_fname__
        self.__conf_fname__ = __conf_fname__
        self.__desc__ = desc

#         self._dType = None
#         self._dTypeList = [
#             'RDD',     # spark resilient distributed dataset
#             'SDF',     # spark DataFrame
#             'PANDAS',  # pandas dataframe
#             'ARRAY',   # numpy array
#             'DICT',    # data dictionary
#         ]

#         ''' Initialize spark session parameters '''
#         self._homeDir = None
#         self._binDir = None
#         self._config = None
#         self._jarDir = None
#         self._appName = None
#         self._master = None
#         self._rwFormat = None
#         self._session = None
#         self._saveMode = None

#         ''' Initialize property var to hold the data '''
#         self._data = None
        

        __s_fn_id__ = "__init__"

        ''' initiate to load app.cfg data '''
        global logger
        global pkgConf
#         global appConf
        global aggList_
        aggList_ = [
            'sum',
            'avg','average',
            'stddev','stdv','standard deviation',
            'mean',
            'median',
            'mode',
            'max','maximum',
            'min','minimum',
        ]

        try:
            self.cwd=os.path.dirname(__file__)
            pkgConf = configparser.ConfigParser()
            pkgConf.read(os.path.join(self.cwd,__ini_fname__))

            self.rezHome = pkgConf.get("CWDS","REZAWARE")
            sys.path.insert(1,self.rezHome)
            from rezaware import Logger as logs

#             ''' Set the utils root directory '''
#             self.pckgDir = pkgConf.get("CWDS",self.__package__)
#             self.appDir = pkgConf.get("CWDS",self.__app__)
#             ''' get the path to the input and output data '''
#             self.dataDir = pkgConf.get("CWDS","DATA")

#             appConf = configparser.ConfigParser()
#             appConf.read(os.path.join(self.appDir, self.__conf_fname__))

            ''' innitialize the logger '''
            logger = logs.get_logger(
                cwd=self.rezHome,
                app=self.__app__, 
                module=self.__module__,
                package=self.__package__,
                ini_file=self.__ini_fname__)
            ''' set a new logger section '''
            logger.info('########################################################')
            logger.info("%s %s",self.__name__,self.__package__)
        
            logger.debug("%s initialization for %s module package %s %s done.\nStart workloads: %s."
                         %(self.__app__,
                           self.__module__,
                           self.__package__,
                           self.__name__,
                           self.__desc__))

        except Exception as err:
            logger.error("%s %s \n",__s_fn_id__, err)
            logger.debug(traceback.format_exc())
            print("[Error]"+__s_fn_id__, err)

        return None
    ''' Function --- IMPUTE DATA ---

            author: <nuwan.waidyanatha@rezgateway.com>
    '''
    @staticmethod
    def impute_data(
#         self,
        data,
        column_subset:list=[],
        strategy:str="mean",
        **kwargs
    ) -> DataFrame:
        """
        Description:
            The impute function leverages the pyspark Imputer class. Based on the specified
            numeric columns or all detected numeric colums, a stretegy set in the function
            parameter, or default mean strategy is applied.
        Attributes:
            data - must be a valid pyspark dataframe
            column_subset:list=[],
            strategy:str="mean",
            **kwargs
        """

        __s_fn_id__ = "function <impute_data>"
        _data = None

        try:
            ''' set and validate data '''
            if not isinstance(data,DataFrame):
                raise AttributeError("Invalid data; must be a valid pyspark dataframe")
            ''' validate column_subset, if none imupte all numeric columns '''
            if len(column_subset) > 0:
                non_num_cols = len([col_ for col_ in column_subset if
                                    data.select(col_).dtypes[0][1] !="string"])
                if non_num_cols < len(column_subset):
                    raise AttributeError("%d invalid non-numeric columns in input var: column_subset"
                                         % len(column_subset)-non_num_cols)
            elif column_subset is None or column_subset==[]:
                column_subset = [col_ for col_ in data.columns if
                                 data.select(col_).dtypes[0][1] !="string"]
            else:
                raise RuntimeError("Something was wrong validating column_subset")

            ''' validate strategy '''
            _strategy = strategy
            if not strategy.lower() in ['mean','median','mode']:
                _strategy = 'mean'
                logger.warning("Invalid strategy %s, reverting to default strategy = %s"
                               ,strategy,_strategy)
            ''' apply imputation '''
            imputer = Imputer(inputCols=column_subset,
                              outputCols=[col_ for col_ in column_subset]
                             ).setStrategy(_strategy)
            _data = imputer.fit(data).transform(data)
#             self._data = imputer.fit(data).transform(data)

        except Exception as err:
            logger.error("%s %s \n",__s_fn_id__, err)
            print("[Error]"+__s_fn_id__, err)
            print(traceback.format_exc())

#         return self._data
        return _data

    ''' Function --- COUNT COLUMN NULLS ---

            author: <nuwan.waidyanatha@rezgateway.com>
    '''
    @staticmethod
    def count_column_nulls(
#         self,
        data,
        column_subset:list=[],
        **kwargs,
    ) -> DataFrame:

        __s_fn_id__ = "function <count_column_nulls>"
        _nan_counts_sdf = None

        try:
            ''' drop any columns not specified in column_subset; else use all '''
            if len([col_ for col_ in column_subset if col_ not in data.columns]) > 0:
                column_subset = data.columns

            _nan_counts_sdf = data.select([F.count(F.when(F.col(c).contains('None') | \
                                        F.col(c).contains('NULL') | \
                                        (F.col(c) == '' ) | \
                                        F.col(c).isNull() | \
                                        F.isnan(c), c )).alias(c)
                                for c in column_subset])

            if _nan_counts_sdf.count() > 0:
                logger.debug("NULL count completed for %d columns",len(_nan_counts_sdf.columns))

        except Exception as err:
            logger.error("%s %s \n",__s_fn_id__, err)
            print("[Error]"+__s_fn_id__, err)
            print(traceback.format_exc())

        return _nan_counts_sdf

    
    ''' Function --- PIVOT DATA ---

            author: <nuwan.waidyanatha@rezgateway.com>
    '''
    @staticmethod
    def pivot_data(
        data,   # a valid pyspark DataFrame
        group_columns, # uses the columns in the grouby extension
        pivot_column,  # column distinct values are used to create the pivot columns
        agg_column,    # the column to apply the sum, avg, stdv aggregation
        **kwargs,      # defines selected pivot col names, aggregation function, etc
    ) -> DataFrame:
        """
        Description:
            Creates a grouped by and pivoted dataframe. The numeric columns will be
            aggregated by a sum by default; unless specified as a kwargs
        Attributes:
            data (DataFrame) a valid pyspark dataframe
            **kwargs
                "AGGREGATE" - the aggregation function sum, mean, avg, min, max,...
                "PIVCOLUMNS" - create pivot table columns for specified values
                ""
        Returns:
            _piv_data (DataFrame)
        """
        __s_fn_id__ = "function <pivot_data>"
        _piv_data = None

        try:
            ''' validate input attributes '''
            if not isinstance(data,DataFrame) and data.count() > 0:
                raise AttributeError("Attribute data must be a valida pyspark dataframe.")
            if group_columns not in data.columns:
                raise AttributeError("Invalid group_columns: %s. Attribute value must be in %s"
                                     % (str(group_columns),str(data.columns)))
            if pivot_column not in data.columns:
                raise AttributeError("Invalid pivot_column: %s. Attribute value must be in %s"
                                     % (pivot_column,str(data.columns)))
            if agg_column not in data.columns:
                raise AttributeError("Invalid agg_column: %s. Attribute value must be in %s"
                                     % (str(agg_column),str(data.columns)))

            _piv_col_names = [x[0] for x in
                              data.dropDuplicates([pivot_column])
                              .select(pivot_column)
                              .collect()]
            if "PIVCOLUMNS" in  kwargs.keys() and kwargs['PIVCOLUMNS'] in _piv_col_names:
                _piv_col_names = kwargs['PIVCOLUMNS']
            logger.debug("Pivot columns: %s",_piv_col_names)
            _agg = 'sum'
            if "AGGREGATE" in kwargs.keys() and kwargs['AGGREGATE'] in aggList_:
                _agg = kwargs['AGGREGATE'].lower()

            logger.debug("Transposing %d rows groupby %s to pivot with "+\
                         "distinct values in %s and %s aggregation on column(s): %s"
                         ,data.count(),str(group_columns).upper()
                         ,str(pivot_column).upper(),_agg.upper(),str(agg_column))
            if _agg == 'sum':
                _piv_data = data.groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .sum(agg_column)
            elif _agg == 'mean':
                _piv_data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .mean(agg_column)
            elif _agg == 'average' or 'avg':
                _piv_data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .avg(agg_column)
            elif _agg == 'standard deviation' or 'stdv' or 'stddev':
                _piv_data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .stddev(agg_column)
            elif _agg == 'median' or 'med':
                _piv_data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .median(agg_column)
            elif _agg == 'mode' or 'mod':
                _piv_data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .mode(agg_column)
            elif _agg == 'maximum' or 'max':
                _data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .max(agg_column)
            elif _agg == 'minimum' or 'min':
                _piv_data = data\
                        .groupBy(group_columns)\
                        .pivot(pivot_column, _piv_col_names)\
                        .min(agg_column)
            else:
                raise AttributeError("Aggregation to be included in the future.")

        except Exception as err:
            logger.error("%s %s \n",__s_fn_id__, err)
            print("[Error]"+__s_fn_id__, err)
            print(traceback.format_exc())

        return _piv_data


    ''' Function --- UNPIVOT TABLE ---
            TODO : where_cols = generate where statement from a list of multiple columns
                   and/or kwargs that specify columns and conditions
            author: <nuwan.waidyanatha@rezgateway.com>
    '''
    @staticmethod
    def unpivot_table(
        table,   # a valid pyspark DataFrame
        unpivot_columns:list=[], # columns to transpose into rows
        index_column:str="",     # selected key column
        value_columns:list=[],   # column name to include the values
        where_cols:str="",       # columns to create where clause statement
        **kwargs,      #
    ) -> DataFrame:
        """
        Description:
            Takes a valid dataframe and a set of columns to transpose them into rows
        Attributes:
            table (DataFrame) a valid pyspark dataframe
            index_column - specifies the key column
            value_column - specifies the column with values
            unpivot_columns - list of columns to transpose to rows
            **kwargs

        Returns:
            _unpiv_data (DataFrame)
        """
        __s_fn_id__ = "function <unpivot_table>"
        _unpiv_data = None
        where_expr = None
        _l_unpiv_cols = []

        try:
            _tbl_cols = table.columns
            ''' validate input attributes '''
            if not isinstance(table,DataFrame) and table.count() > 0:
                raise AttributeError("Attribute data must be a valida pyspark dataframe.")

            if len(list(set(unpivot_columns) & set(_tbl_cols)))<len(unpivot_columns):
                raise AttributeError("Invalid unpivot_columns: %s.\n\nAttribute value must be in %s"
                                     % (str(unpivot_columns),str(_tbl_cols)))
            if index_column not in _tbl_cols or index_column in unpivot_columns:
                raise AttributeError("Invalid index_column: %s must be a column other than %s "
                                     % (index_column,str(unpivot_columns)))
            if value_columns==[]:
                raise AttributeError("Invalid value_column %s" % (value_column))
            if "".join(where_cols).split() != "":
                where_expr = f"{where_cols} is not null"
            else:
                where_expr = f"where 1=1"

            ''' create the column str val pairs list '''
            _unpiv_col_vals = ",".join(unpivot_columns).split(",")
            for _col in range(len(unpivot_columns)):
                _l_unpiv_cols.append("'{}'".format(unpivot_columns[_col])+","+_unpiv_col_vals[_col])
            _s_col_pairs=",".join(_l_unpiv_cols)
            ''' set the as columns expression '''
            _l_as_cols = ",".join(value_columns).split(",")
            _s_as_cols = ",".join(_l_as_cols)

            unpiv_expr="stack({0},{1}) as "\
                        .format(len(unpivot_columns),_s_col_pairs)+f"({_s_as_cols})"
            _unpiv_data = table.select(index_column, F.expr(unpiv_expr)).where(where_expr)

        except Exception as err:
            logger.error("%s %s \n",__s_fn_id__, err)
            print("[Error]"+__s_fn_id__, err)
            print(traceback.format_exc())

        return _unpiv_data



#     ''' Function --- PREVIOUS VAL DIFFERENCE ---

#             author: <nuwan.waidyanatha@rezgateway.com>
#     '''
#     @staticmethod
#     def prev_val_diff(
#         data:DataFrame,
#         num_column:str,
#         part_column:str,
#         **kwargs,
#     ) -> DataFrame:
#         """
#         Description:
#             for a given numeric column, the function computes the difference between
#             the current cell and the previous cell
#         Attributes:
#             data (DataFrame) a valid pyspark dataframe
#             column - specifies column to compute the difference
#             **kwargs
#                 DIFFCOLNAME - the column name
#         Returns:
#         """

#         __s_fn_id__ = "function <unpivot_table>"
#         _diff_data = None
#         prev_value = "prev_value"

#         try:
#             if data.count() <= 2:
#                 raise AttributeError("Dataframe must have, at least, 2 rows to compute the difference ")
#             if num_column not in data.columns and \
#                 not isinstance(data.num_column,int) and\
#                 not isinstance(data.num_column,float):
#                 raise AttributeError("%s must be a numeric dataframe column" % num_column)
#             if part_column not in data.columns:
#                 raise AttributeError("%s must be a column in the dataframe: %s" 
#                                      % (num_column,data.columns))
#             if "DIFFCOLNAME" in kwargs.keys():
#                 prev_value = kwargs['DIFFCOLNAME']

#             _win = Window.partitionBy(part_column).orderBy(part_column)
#             _diff_data = data.withColumn(prev_value, F.lag(data[num_column]).over(_win))
#             _diff_data = _diff_data.withColumn("diff",\
#                                     F.when(\
#                                       F.isnull(_diff_data[num_column] - _diff_data[prev_value]), 0)\
#                                       .otherwise(_diff_data[num_column] - _diff_data[prev_value]))

#         except Exception as err:
#             logger.error("%s %s \n",__s_fn_id__, err)
#             print("[Error]"+__s_fn_id__, err)
#             print(traceback.format_exc())

#         return _diff_data


    ''' Function --- DROP DUPLICATES ---

            author: <nuwan.waidyanatha@rezgateway.com>
    '''
    @staticmethod
    def drop_duplicates(
        data
    ) -> DataFrame:
        """
        Description:
            To Be Developed
        Attributes:
        Returns:
        """

        try:
            ''' drop duplicates 
                TODO - move to a @staticmethod '''
            if "DROPDUPLICATES" in kwargs.keys() and kwargs['DROPDUPLICATES']:
                _unique_sdf = data.distinct()
                logger.debug("Removed duplicates, reduced dataframe with %d rows",_unique_sdf.count())

            ''' convert to pandas dataframe 
                TODO - move to @staticmethod '''
            if 'TOPANDAS' in kwargs.keys() and kwargs['TOPANDAS']:
                _unique_sdf = _unique_sdf.toPandas()
                logger.debug("Converted pyspark dataframe to pandas dataframe with %d rows"
                             % _unique_sdf.shape[0])
        except Exception as err:
            logger.error("%s %s \n",__s_fn_id__, err)
            print("[Error]"+__s_fn_id__, err)
            print(traceback.format_exc())

        return _unique_sdf