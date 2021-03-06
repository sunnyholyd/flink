################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

from abc import ABCMeta

from pyflink.java_gateway import get_gateway
from pyflink.table import Table
from pyflink.util import type_utils, utils

__all__ = [
    'BatchTableEnvironment',
    'StreamTableEnvironment',
    'TableEnvironment'
]


class TableEnvironment(object):
    """
    The abstract base class for batch and stream TableEnvironments.
    """

    __metaclass__ = ABCMeta

    def __init__(self, j_tenv):
        self._j_tenv = j_tenv

    def from_table_source(self, table_source):
        """
        Creates a table from a table source.

        :param table_source: The table source used as table.
        :return: The result table.
        """
        return Table(self._j_tenv.fromTableSource(table_source._j_table_source))

    def register_table(self, name, table):
        """
        Registers a :class:`Table` under a unique name in the TableEnvironment's catalog.
        Registered tables can be referenced in SQL queries.

        :param name: The name under which the table will be registered.
        :param table: The table to register.
        """
        self._j_tenv.registerTable(name, table._java_table)

    def register_table_source(self, name, table_source):
        """
        Registers an external :class:`TableSource` in this :class:`TableEnvironment`'s catalog.
        Registered tables can be referenced in SQL queries.

        :param name: The name under which the :class:`TableSource` is registered.
        :param table_source: The :class:`TableSource` to register.
        """
        self._j_tenv.registerTableSource(name, table_source._j_table_source)

    def register_table_sink(self, name, field_names, field_types, table_sink):
        """
        Registers an external :class:`TableSink` with given field names and types in this
        :class:`TableEnvironment`'s catalog.
        Registered sink tables can be referenced in SQL DML statements.

        :param name: The name under which the :class:`TableSink` is registered.
        :param field_names: The field names to register with the :class:`TableSink`.
        :param field_types: The field types to register with the :class:`TableSink`.
        :param table_sink: The :class:`TableSink` to register.
        """
        gateway = get_gateway()
        j_field_names = utils.to_jarray(gateway.jvm.String, field_names)
        j_field_types = utils.to_jarray(
            gateway.jvm.TypeInformation,
            [type_utils.to_java_type(field_type) for field_type in field_types])
        self._j_tenv.registerTableSink(name, j_field_names, j_field_types, table_sink._j_table_sink)

    def scan(self, *table_path):
        """
        Scans a registered table and returns the resulting :class:`Table`.
        A table to scan must be registered in the TableEnvironment. It can be either directly
        registered as TableSource or Table.

        Examples:

        Scanning a directly registered table
        ::
            >>> tab = t_env.scan("tableName")

        Scanning a table from a registered catalog
        ::
            >>> tab = t_env.scan("catalogName", "dbName", "tableName")

        :param table_path: The path of the table to scan.
        :throws: Exception if no table is found using the given table path.
        :return: The resulting :class:`Table`
        """
        gateway = get_gateway()
        j_table_paths = utils.to_jarray(gateway.jvm.String, table_path)
        j_table = self._j_tenv.scan(j_table_paths)
        return Table(j_table)

    def execute(self, job_name=None):
        """
        Triggers the program execution.

        :param job_name: Optional, desired name of the job.
        """
        if job_name is not None:
            self._j_tenv.execEnv().execute(job_name)
        else:
            self._j_tenv.execEnv().execute()

    @classmethod
    def get_table_environment(cls, table_config):
        """
        Returns a :class:`StreamTableEnvironment` or a :class:`BatchTableEnvironment`
        which matches the :class:`TableConfig`'s content.

        :type table_config: The TableConfig for the new TableEnvironment.
        :return: Desired :class:`TableEnvironment`.
        """
        gateway = get_gateway()
        if table_config.is_stream:
            j_execution_env = gateway.jvm.StreamExecutionEnvironment.getExecutionEnvironment()
            j_tenv = gateway.jvm.StreamTableEnvironment.create(j_execution_env)
            t_env = StreamTableEnvironment(j_tenv)
        else:
            j_execution_env = gateway.jvm.ExecutionEnvironment.getExecutionEnvironment()
            j_tenv = gateway.jvm.BatchTableEnvironment.create(j_execution_env)
            t_env = BatchTableEnvironment(j_tenv)

        if table_config.parallelism is not None:
            t_env._j_tenv.execEnv().setParallelism(table_config.parallelism)

        return t_env


class StreamTableEnvironment(TableEnvironment):

    def __init__(self, j_tenv):
        self._j_tenv = j_tenv
        super(StreamTableEnvironment, self).__init__(j_tenv)


class BatchTableEnvironment(TableEnvironment):

    def __init__(self, j_tenv):
        self._j_tenv = j_tenv
        super(BatchTableEnvironment, self).__init__(j_tenv)
